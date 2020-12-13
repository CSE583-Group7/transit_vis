# pylint: disable=E1101

"""Gathers data from dynamodb database and plots it to a Folium Map for display.

This is the main component of the visualization tool. It first gathers data on
all of the segment stored in the dynamodb, then constructs a Folium map which
contains both the route segments and census tract-level socioeconomic data taken
from the American Community Survey. The map is saved as an html file and opened
in a web browser automatically.
"""


import boto3
import branca.colormap as cm
import numpy as np

import config as cfg
import vis_functions


def connect_to_dynamo_table(table_name):
    """Connects to the dynamodb table specified using details from config.py.

    Uses the AWS login information stored in config.py to attempt a connection
    to dynamodb using the boto3 library, then creates a connection to the
    specified table.

    Args:
        table_name: The name of the table on the dynamodb resource to connect.

    Returns:
        A boto3 Table object pointing to the dynamodb table specified.
    """
    dynamodb = boto3.resource(
        'dynamodb',
        region_name=cfg.REGION,
        aws_access_key_id=cfg.ACCESS_ID,
        aws_secret_access_key=cfg.ACCESS_KEY)
    table = dynamodb.Table(table_name)
    return table

def dump_table(dynamodb_table):
    """Downloads the contents of a dynamodb table and returns them as a list.

    Iterates through the contents of a dynamodb scan() call, which returns a
    LastEvaluatedKey until there are no results left in the scan. Appends each
    chunk of data returned by scan to an array for further use.

    Args:
        dynamodb_table: A boto3 Table object from which all data will be read
            into memory and returned.

    Returns:
        A list of items downloaded from the dynamodb table. In this case, each
        item is a bus route as generated in initialize_db.py.
    """
    result = []
    response = dynamodb_table.scan()
    result.extend(response['Items'])
    while 'LastEvaluatedKey' in response.keys():
        response = dynamodb_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        result.extend(response['Items'])
    return result

def table_to_lookup(table):
    """Converts the contents of a dynamodb table to a dictionary for reference.

    Uses dump_table to download the contents of a specified table, then creates
    a route lookup dictionary where each key is (route id, express code) and
    contains elements for avg_speed, and historic_speeds.

    Args:
        table: A boto3 Table object from which all data will be read
            into memory and returned.

    Returns:
        A dictionary with (route id, segment id) keys and average speed (num),
        historic speeds (list), and local express code (str) data.
    """
    # Put the data in a dictionary to reference when adding speeds to geojson
    items = dump_table(table)
    route_lookup = {}
    for item in items:
        if 'avg_speed_m_s' in item.keys():
            route_id = int(item['route_id'])
            local_express_code = item['local_express_code']
            route_lookup[(route_id, local_express_code)] = {
                'avg_speed_m_s': float(item['avg_speed_m_s']),
                'historic_speeds': item['historic_speeds']
            }
    return route_lookup

def main_function(
        table_name,
        s0801_file,
        s1902_file,
        segment_file,
        census_file):
    """Combines ACS data, downloads speed data, and plots map of results.

    Build the final map by first preparing ACS and dynamodb data, then plotting
    the data using the Folium library and save it to a .html file and open with
    the user's web browser.

    Args:
        table_name: The name of the dynamodb table containing speed data.
        s0801_file: A string path to the location of the raw s0801 data, not
            including file type ending (.csv).
        s1902_file: A string path to the location of the raw s1902 data, not
            including file type ending (.csv).
        segment_file: A string path to the geojson file generated by
            initialize_db.py that contains route coordinate data.
        census_file: A string path to the geojson TIGER shapefile as
            downloaded from the ACS, containing polygon data for census tracts
            in the state of Washington.

    Returns:
        1 when done writing and opening the Folium map .html file.
    """
    # Combine census tract data from multiple ACS tables for Seattle
    print("Modifying and writing census data...")
    vis_functions.write_census_data_to_csv(s0801_file, s1902_file, census_file)

    # Connect to dynamodb
    print("Connecting to dynamodb...")
    table = connect_to_dynamo_table(table_name)

    # Query the dynamoDB for all speed data
    print("Getting speed data from dynamodb...")
    speed_lookup = table_to_lookup(table)

    print("Writing speed data to segments for visualization...")
    speeds = vis_functions.write_speeds_to_map_segments(speed_lookup, segment_file)

    # Create the color mapping for speeds
    print("Generating map...")
    linear_cm = cm.LinearColormap(
        ['red', 'yellow', 'green'],
        vmin=0.0,
        vmax=np.ceil(np.percentile(speeds[speeds > 0.0], 95)))

    f_map = vis_functions.generate_folium_map(segment_file, census_file, linear_cm)
    print("Saving map...")
    vis_functions.save_and_view_map(f_map, 'output_map.html')
    return 1
