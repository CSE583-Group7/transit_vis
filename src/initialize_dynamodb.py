"""Builds a network of segments from individual bus routes and uploads them.

This module is intended to be run as a setup prior to using the visualization
tool. It takes a geojson file with complete bus routes and breaks them into
individual segments, before rejoining them to a specified minimum length and
uploading those segments to a dynamodb database. Once this has been done, the
summarize_rds.py module can aggregate bus speeds to these recreated segments.
"""


import json
import os

import boto3
import numpy as np

import config as cfg


def sort_and_save_exploded_lines(exploded_geojson_name, output_folder):
    """Sorts geojson bus segments based on route id.

    Sifts through a geojson file that contains exploded route segments that are
    not necessarily in order. Sorts those segments according to their route id
    and creates a geojson file for each route id in a specified output folder.
    Also creates a list of keys for each route id for reference.
    
    Args:
        exploded_geojson_name: Path to the exploded geojson file that is to be
            uploaded. Must have [properties][ROUTE_ID] and
            [properties][LOCAL_EXPR] elements. Do not include file type ending
                (.geojson etc.).
        output_folder: Path to folder where sorted segments and keys should be
            saved.

    Returns:
        1 if function runs successfully. Also writes keys and labeled segments
        to specified output folder.
    """
    with open(f"{exploded_geojson_name}.geojson", 'r') as f:
        kcm_routes = json.load(f)
    # Sort route data by its route label to make processing it faster
    data = kcm_routes['features']
    label_sorted = {}
    for datapoint in data:
        k = datapoint['properties']['ROUTE_ID']
        if k not in label_sorted.keys():
            label_sorted[k] = [datapoint]
        else:
            label_sorted[k].append(datapoint)
    for key in label_sorted.keys():
        # Open file specific to each label
        with open(f"{output_folder}/label_{key}.json", "w+") as outfile:
            json.dump(label_sorted[key], outfile)
    # Save a list of keys
    with open(f"{output_folder}/labels.json", "w+") as outfile:
        json.dump(list(label_sorted.keys()), outfile)
    return 1

def join_line_segments(input_folder, min_segment_length):
    """Joins exploded lines to recreate segments of specified length.

    Uses the sorted line segments from sort_and_save_exploded_lines to create
    a new set of features. Each feature is a continuous set of segments that all
    share a route id, and is not shorter than the specified segment length.
    These features will be used to aggregate speeds in the dynamodb, and in the
    final Folum visualization.
    
    Args:
        input_folder: Path to the folder specified in sort_and_save where sorted
            line segments and keys can be found.
        min_segment_length: The minimum length that final features should have.

    Returns:
        A tuple containing the list of joined line segments features, a list of
        features that were unable to be rejoined, and the set of keys that were
        used in sorting the features.
    """
    feature_list = []
    isolated_list = []
    keys = []
    with open(f"{input_folder}/labels.json", "r") as keyfile:
        keys = json.load(keyfile)
    for k in keys:
        with open(f"{input_folder}/label_{k}.json", "r") as f:
            data = json.load(f)
            i = 0
            isolated_segments = []
            # Iterate once through the exploded segments with while(i)
            while i < len(data):
                # Continue unless current segment is too short
                if data[i]['properties']['SEG_LENGTH'] > min_segment_length:
                    i += 1
                    continue
                # Remove the short segment from data
                segment = data.pop(i)
                start = segment['geometry']['coordinates'][0]
                end = segment['geometry']['coordinates'][-1]
                flag = False
                # Search full dataset for a connected segment, append if found
                for j in range(0, len(data)):
                    seg2 = data[j]
                    if end == seg2['geometry']['coordinates'][0]:
                        seg2['geometry']['coordinates'].append(
                            segment['geometry']['coordinates'][0])
                        seg2['properties']['SEG_LENGTH'] += segment['properties']['SEG_LENGTH']
                        flag = True
                        break
                    elif start == seg2['geometry']['coordinates'][-1]:
                        seg2['geometry']['coordinates'].append(
                            segment['geometry']['coordinates'][-1])
                        seg2['properties']['SEG_LENGTH'] += segment['properties']['SEG_LENGTH']
                        flag = True
                        break
                if not flag:
                    # The too short segment did not have a match anywhere
                    isolated_segments.append(segment)
        feature_list.extend(data)
        isolated_list.extend(isolated_segments)
    return (feature_list, isolated_list, keys)

def replace_floats(obj):
    """Replaces all data types of a nested structure with strings.

    Dynamodb does not support float values, which will potentially cause
    problems with lat/lon and other long decimals. This function works with json
    styled nested objects to convert all values to strings for uploading.
    
    Args:
        obj: Object with nested dict/list values to convert to strings.

    Returns:
        The same object that was passed, but with all values changed to strings.
    """
    if isinstance(obj, list):
        for i in range(0,len(obj)):
            obj[i] = replace_floats(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_floats(obj[k])
        return obj
    elif isinstance(obj, float):
        if obj % 1 == 0:
            return int(obj)
        else:
            return str(obj)
    else:
        return obj

def json_route_ids_to_keys(kcm_routes):
    """Adds a 0 or 1 to route id based on whether route is local or express.

    Concatenates a 0 to the end of a route id if it is a local route, or a 1 to
    the end of the route id if it is an express route. This allows route id to
    become a unique identifier for every route in the King County Metro network.
    This is necessary because dynamodb only supports composite keys with 2
    values, and the schema uses segment_id as the second value.
    
    Args:
        kcm_routes: A geojson object that has [properties][ROUTE_ID] and
            [properties][LOCAL_EXPR] as the route id and local/express ids
            respectively.

    Returns:
        The same geojson object passed, but with new route ids that contain 1
        additional digit at the end (0 for local, 1 for express).
    """
    for feature in kcm_routes['features']:
        feature['route_id'] = feature['properties']['ROUTE_ID']
        feature['segment_id'] = feature['properties']['SEG_ID']
        if feature['properties']['LOCAL_EXPR'] == 'L':
            feature['route_id'] = int(str(feature['route_id']) + str(0))
        else:
            feature['route_id'] = int(str(feature['route_id']) + str(1))
    return(kcm_routes)

def connect_to_dynamo():
    """Connects to the dynamodb resource specified in config.py.

    Uses the AWS login information stored in config.py to attempt a connection
    to dynamodb using the boto3 library.

    Returns: A boto3 Resource object pointing to dynamodb for the specified
        AWS account.
    """
    try:
        dynamodb = boto3.resource('dynamodb',
                                 region_name=cfg.REGION,
                                 aws_access_key_id=cfg.ACCESS_ID,
                                 aws_secret_access_key=cfg.ACCESS_KEY)
    except:
        pass
    return dynamodb

def create_dynamo_table(dynamodb_resource, table_name):
    """Creates a new table for segments on a specified dynamodb resource.

    Creates a table with the specified name on the specified dynamodb resource.
    The keys are set as route id and segment id, which should identify any
    unique segment in the dataset. Both are set to numeric types. Read/write
    capacity is limited to 20/sec to stay within the AWS free-tier. This is
    necessary but greatly slows down the upload process.
    
    Args:
        dynamodb_resource: A boto3 Resource pointing to the AWS account on which
            the table should be created.
        table_name: A string containing the name for the segments table.

    Returns: A boto3 Table object pointing to the newly created segments table.
    """
    table = dynamodb_resource.create_table(TableName=table_name,
                                          KeySchema=[
                                              {
                                                  'AttributeName': 'route_id',
                                                  'KeyType': 'HASH'
                                              },
                                              {
                                                  'AttributeName': 'segment_id',
                                                  'KeyType': 'RANGE'
                                              }],
                                          AttributeDefinitions=[
                                              {
                                                  'AttributeName': 'route_id',
                                                  'AttributeType': 'N'
                                              },
                                              {
                                                  'AttributeName': 'segment_id',
                                                  'AttributeType': 'N'
                                              }],
                                          ProvisionedThroughput={
                                              'ReadCapacityUnits': 20,
                                              'WriteCapacityUnits': 20
                                          })
    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    return table

def upload_segments_to_dynamo(dynamodb_resource, table_name, kcm_routes):
    """Uploads the segments in a geojson file to a specified dynamodb table.

    Goes thorugh each of the features in a geojson file, and creates a new item
    for that feature on dynamodb. The key is set based on route and segment id.
    A field is created for average speed and initialized to 0. An array field
    is created for past speeds and initialized empty. When summarize_rds.py is
    run, it will append the average daily speed to the historic speeds list and
    set the new average speed to that day's speed.
    
    Args:
        dynamodb_resource: A boto3 Resource pointing to the AWS account on which
            the table should be created.
        table_name: A string containing the name for the segments table.
        kcm_routes: A geojson object containing the features that should be
            uploaded. Each feature must have a [route_id] and a [segment_id]
            property. Although this object also contains all of the geometry,
            only the route and segment ids will be uploaded. The Folium map will
            read the speeds from the databse and rejoin them to this file
            locally for display.

    Returns: 1 when the features are finished uploading to the table.
    """
    table = dynamodb_resource.Table(table_name)
    # Takes about 1hr to do 70,000 features
    with table.batch_writer() as batch:
        for route in kcm_routes['features']:
            batch.put_item(Item={
                          'route_id': route['route_id'],
                          'segment_id': route['segment_id'],
                          'local_express_code': route['properties']['LOCAL_EXPR'],
                          'historic_speeds': [],
                          'avg_speed_m_s': 0})
    return 1

def main_function(exploded_geojson_name,
                 label_folder_name,
                 dynamodb_table_name,
                 min_segment_length):
    """Joins and uploads exploded route segments for a bus network.

    Runs one time to initialize a dynamodb with a set of bus route segments. The
    segments are created from a set of exploded segments. Exploded segments
    contain only straight lines (each segment is simply 2 lat/lon coordinates).
    These are generated using any GIS or spatial manipulation software to break
    apart a shapefile containing all of the routes for a network. In this case,
    the network is the King County Metro network. The route shapefile can be
    found at https://www5.kingcounty.gov/sdc/Metadata.aspx?Layer=transitroute.
    
    Args:
        exploded_geojson_name: Path to the exploded geojson file that is to be
            uploaded. Must have [properties][ROUTE_ID] and
            [properties][LOCAL_EXPR] elements. Do not include file type ending
                (.geojson etc.).
        label_folder_name: Path to the folder where sorted segments and keys
            from the exploded geojson should be stored. 
        table_name: A string containing the name for the segments table.
        min_segment_length: The minimum length (feet) that final features should
            have.

    Returns: An integer of the number of features that were uploaded to the
        database.
    """
    # Create folder to store labels if it doesn't exist
    print("Creating label folder if it doens't exist already...")
    try:
        os.mkdir(label_folder_name, mode = 0o777)
    except FileExistsError:
        pass
    
    # Read in exploded bus shapefiles, sort them, and join shorter segments
    print("Sorting and saving lines...")
    sort_and_save_exploded_lines(exploded_geojson_name, label_folder_name)
    print("Joining lines into feature list...")
    feature_list, isolated_list, keys = join_line_segments(label_folder_name,
                                                          min_segment_length)
    print(f"{len(isolated_list)} features were isolated.")
    print("Saving feature list to KCM geojson...")
    with open(f"{exploded_geojson_name}.geojson", 'r') as f:
        kcm_routes = json.load(f)
    
    # Replace the features with our newly joined segments
    kcm_routes['features'] = feature_list
    
    # Add code for express or local route
    kcm_routes = json_route_ids_to_keys(kcm_routes)
    
    # Turn all float values (coordinates mostly) into strings in the geojson
    kcm_routes = replace_floats(kcm_routes)
    
    # Write the modified segments to geojson, this will be used again in Folium
    with open(f"{exploded_geojson_name}_modified.geojson", 'w+') as f:
        json.dump(kcm_routes, f)

    # Upload the modified segments to a newly created dynamodb table
    print("Connecting to Dynamodb...")
    dynamodb_resource = connect_to_dynamo()
    print("Creating new table...")
    create_dynamo_table(dynamodb_resource, dynamodb_table_name)
    print("Uploading segments to table...")
    upload_segments_to_dynamo(dynamodb_resource,
                             dynamodb_table_name,
                             kcm_routes)

    # Return the number of features that are in the kcm data
    return len(kcm_routes['features'])    

# Main program starts here
num_features = main_function('../data/kcm_routes_exploded',
                            '../data/sorted_labels',
                            'KCM_Bus_Routes_Modified_Production',
                            720)
print(f"{num_features} features in data uploaded to dynamodb")
