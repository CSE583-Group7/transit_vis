import json
import os

import boto3
import numpy as np

import config as cfg


def sort_and_save_exploded_lines(exploded_geojson_name, output_folder):
    with open(f"{exploded_geojson_name}.geojson", 'r') as f:
        kcm_routes = json.load(f)

    # Sort route data by its route label to make processing it in the next step faster
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
    # Matching route segments to get segments that are connected and larger than min_segment_length meters
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
            while i < len(data):
                if data[i]['properties']['SEG_LENGTH'] > min_segment_length:
                    i += 1
                    continue
                segment = data.pop(i)
                start = segment['geometry']['coordinates'][0]
                end = segment['geometry']['coordinates'][-1]
                flag = False
                for j in range(0, len(data)):
                    seg2 = data[j]
                    if end == seg2['geometry']['coordinates'][0]:
                        seg2['geometry']['coordinates'].append(segment['geometry']['coordinates'][0])
                        seg2['properties']['SEG_LENGTH'] += segment['properties']['SEG_LENGTH']
                        flag = True
                        break
                    elif start == seg2['geometry']['coordinates'][-1]:
                        seg2['geometry']['coordinates'].append(segment['geometry']['coordinates'][-1])
                        seg2['properties']['SEG_LENGTH'] += segment['properties']['SEG_LENGTH']
                        flag = True
                        break
                if not flag:
                    isolated_segments.append(segment)
            feature_list.extend(data)
            isolated_list.extend(isolated_segments)
    return (feature_list, isolated_list, keys)

# Function that iterates through an obj containing nested dicts and lists to replace all floats with strings
# This is necessary because Dynamodb does not support float values
def replace_floats(obj):
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
    # Add the local express to the route id to create unique key for each segment (dynamodb only can have a 2-composite key)
    for feature in kcm_routes['features']:
        feature['route_id'] = feature['properties']['ROUTE_ID']
        feature['segment_id'] = feature['properties']['SEG_ID']
        if feature['properties']['LOCAL_EXPR'] == 'L':
            feature['route_id'] = int(str(feature['route_id']) + str(0))
        else:
            feature['route_id'] = int(str(feature['route_id']) + str(1))
    return(kcm_routes)

def connect_to_dynamo():
    # Set up the connection to the Dynamodb database
    try:
        dynamodb = boto3.resource('dynamodb',
                                 region_name=cfg.REGION,
                                 aws_access_key_id=cfg.ACCESS_ID,
                                 aws_secret_access_key=cfg.ACCESS_KEY)
    except:
        pass
    return dynamodb

def create_dynamo_table(dynamodb_resource, table_name):
    # Create table with one key on the route_id for each route
    # The rest of the table structure can be open, only required values on insert are keys
    table = dynamodb_resource.create_table(TableName=table_name,
                                          KeySchema=[
                                              {
                                                  'AttributeName': 'route_id',
                                                  'KeyType': 'HASH'
                                              },
                                              {
                                                  'AttributeName': 'segment_id',
                                                  'KeyType': 'RANGE'
                                              }
                                          ],
                                          AttributeDefinitions=[
                                              {
                                                  'AttributeName': 'route_id',
                                                  'AttributeType': 'N'
                                              },
                                              {
                                                  'AttributeName': 'segment_id',
                                                  'AttributeType': 'N'
                                              }
                                          ],
                                          ProvisionedThroughput={
                                              'ReadCapacityUnits': 20,
                                              'WriteCapacityUnits': 20
                                          })
    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    return table

def upload_segments_to_dynamo(dynamodb_resource, table_name, kcm_routes):
    table = dynamodb_resource.Table(table_name)
    # Takes about 1hr to do 70,000 features; capacity constrained to stay in AWS free-tier
    with table.batch_writer() as batch:
        for route in kcm_routes['features']:
            batch.put_item(Item={
                'route_id': route['route_id'],
                'segment_id': route['segment_id'],
                'local_express_code': route['properties']['LOCAL_EXPR'],
                'historic_speeds': [],
                'avg_speed_m_s': 0
            })
    return 1

def main_function(exploded_geojson_name, label_folder_name, dynamodb_table_name, min_segment_length):
    # Create folder to store labels if it doesn't exist
    try:
        os.mkdir(label_folder_name, mode = 0o777)
    except FileExistsError:
        pass
    # Read in exploded bus shapefiles, sort them, and join shorter segments to make a new dataset
    print("Sorting and saving lines...")
    sort_and_save_exploded_lines(exploded_geojson_name, label_folder_name)
    print("Joining lines into feature list...")
    feature_list, isolated_list, keys = join_line_segments(label_folder_name, min_segment_length)
    print("Saving feature list to KCM geojson...")
    with open(f"{exploded_geojson_name}.geojson", 'r') as f:
        kcm_routes = json.load(f)
    # Replace the features with our newly joined segments
    kcm_routes['features'] = feature_list
    # Add code for express or local route
    kcm_routes = json_route_ids_to_keys(kcm_routes)
    # Turn all float values (coordinates mostly) into strings in the routes geojson
    kcm_routes = replace_floats(kcm_routes)
    # Write the modified segments to geojson, this will be used again in Folium (segments in folium and dynamodb match)
    with open(f"{exploded_geojson_name}_modified.geojson", 'w+') as f:
        json.dump(kcm_routes, f)

    # Upload the modified segments to a newly created dynamodb table
    print("Connecting to Dynamodb...")
    dynamodb_resource = connect_to_dynamo()
    print("Creating new table...")
    create_dynamo_table(dynamodb_resource, dynamodb_table_name)
    print("Uploading segments to table...")
    upload_segments_to_dynamo(dynamodb_resource, dynamodb_table_name, kcm_routes)

    # Return the number of features that are in the kcm data
    return len(kcm_routes['features'])    

num_features = main_function('../data/kcm_routes_exploded', '../data/sorted_labels', 'KCM_Bus_Routes_Modified_Production', 720)
print(f"{num_features} features in data uploaded to dynamodb")
