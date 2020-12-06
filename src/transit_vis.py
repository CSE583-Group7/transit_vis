"""Gathers data from dynamodb database and plots it to a Folium Map for display.

This is the main component of the visualization tool. It first gathers data on
all of the segment stored in the dynamodb, then constructs a Folium map which
contains both the route segments and census tract-level socioeconomic data taken
from the American Community Survey. The map is saved as an html file and opened
in a web browser automatically.
"""


from collections import defaultdict
import webbrowser

import boto3
from boto3.dynamodb.conditions import Key, Attr
import branca.colormap as cm
import folium
import json
import numpy as np
import pandas as pd

import config as cfg


def write_census_data_to_csv(s0801_path, s1902_path, tract_shapes_path):
    # Read in the two tables that were taken from the ACS data portal website
    s0801_df = pd.read_csv(f"{s0801_path}.csv")
    s1902_df = pd.read_csv(f"{s1902_path}.csv")
    # Filter each table to only variables we are interested in, rename columns to be more descriptive
    commuters_df = s0801_df[['GEO_ID', 'NAME', 'S0801_C01_001E', 'S0801_C01_009E']]
    commuters_df.columns = ['GEO_ID', 'NAME', 'total_workers', 'workers_using_transit']
    commuters_df = commuters_df.loc[1:len(commuters_df),:]
    commuters_df['GEO_ID'] = commuters_df['GEO_ID'].str[-11:]
    households_df = s1902_df[['GEO_ID', 'NAME', 'S1902_C01_001E', 'S1902_C03_001E', 'S1902_C02_008E', 'S1902_C02_020E', 'S1902_C02_021E']]
    households_df.columns = ['GEO_ID', 'NAME', 'total_households', 'mean_income', 'percent_w_assistance', 'percent_white', 'percent_black_or_african_american']
    households_df = households_df.loc[1:len(households_df),:]
    households_df['GEO_ID'] = households_df['GEO_ID'].str[-11:]
    # Combine datasets on their census tract ID and write to .csv file for the visualization
    final_df = pd.merge(commuters_df, households_df, on='GEO_ID').drop(columns=['NAME_x', 'NAME_y'])
    final_df.to_csv(f"{tract_shapes_path}_tmp.csv", index=False)
    return 1

def connect_to_dynamo_table(table_name):
    # Set up the connection to the Dynamodb database
    try:
        dynamodb = boto3.resource('dynamodb',
                                 region_name=cfg.REGION,
                                 aws_access_key_id = cfg.ACCESS_ID,
                                 aws_secret_access_key = cfg.ACCESS_KEY)
        table = dynamodb.Table(table_name)
    except:
        pass
    return table

def dump_table(dynamodb_table): 
    result = []
    response = dynamodb_table.scan()
    result.extend(response['Items'])
    while 'LastEvaluatedKey' in response.keys():
        response = dynamodb_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        result.extend(response['Items'])
    return result

def table_to_lookup(table):
    # Put the data in a dictionary to easily reference from when adding speeds to the geojson shapes
    items = dump_table(table)
    route_lookup = {}
    for item in items:
        if 'avg_speed_m_s' in item.keys():
            route_id = int(item['route_id'])
            segment_id = int(item['segment_id'])
            route_lookup[(route_id, segment_id)] = {'avg_speed_m_s': float(item['avg_speed_m_s']),
                                                'local_express_code': str(item['local_express_code']),
                                                'historic_speeds': item['historic_speeds']}
    return route_lookup

def write_speeds_to_map_segments(speed_lookup, segment_file):
    # Read in geojson route geoJson, add a new property for avg speed, keep track of all speeds
    speeds = np.ones(0)
    with open(f"{segment_file}.geojson", 'r') as f:
        kcm_routes = json.load(f)
    # Check if each geojson feature has a speed in the database
    for feature in kcm_routes['features']:
        route_id = feature['route_id']
        segment_id = feature['segment_id']
        if (route_id, segment_id) in speed_lookup.keys():
            feature['properties']['AVG_SPEED_M_S'] = speed_lookup[(route_id, segment_id)]['avg_speed_m_s']
            speeds = np.append(speeds, speed_lookup[(route_id, segment_id)]['avg_speed_m_s'])
        else:
            feature['properties']['AVG_SPEED_M_S'] = 0
    with open(f"{segment_file}_w_speeds_tmp.geojson", 'w+') as f:
        json.dump(kcm_routes, f, indent=2)
    return speeds

def generate_folium_map(segment_file, census_file, colormap):
    # Read in route shapefile and give it the style function above
    kcm_routes = folium.GeoJson(f"{segment_file}_w_speeds_tmp.geojson",
                                style_function=lambda feature: {
                                    'color': colormap(feature['properties']['AVG_SPEED_M_S']),
                                    'weight': 2}
                                )
    # Read in the census data/shapefile and create a choropleth based on income
    seattle_tracts_df = pd.read_csv(f"{census_file}_tmp.csv")
    seattle_tracts_df['GEO_ID'] = seattle_tracts_df['GEO_ID'].astype(str)
    seattle_tracts_df['mean_income'] = pd.to_numeric(seattle_tracts_df['mean_income'], errors='coerce')
    seattle_tracts_df = seattle_tracts_df.dropna()
    seattle_tracts = folium.Choropleth(geo_data=f"{census_file}.geojson",
                                    name='Socioeconomic Data',
                                    data=seattle_tracts_df,
                                    columns=['GEO_ID', 'mean_income'],
                                    key_on='feature.properties.GEOID10',
                                    fill_color='PuBu',
                                    fill_opacity=0.7,
                                    line_opacity=0.4,
                                    legend_name='mean income'
                                    )
    # Draw map using the updated kcm_routes with avg speed data and choropleth from census data
    m = folium.Map(location=[47.606209, -122.332069],
                zoom_start=11,
                prefer_canvas=True
                )
    seattle_tracts.add_to(m)
    kcm_routes.add_to(m)
    colormap.caption = 'Average Speed (m/s)'
    colormap.add_to(m)
    folium.LayerControl().add_to(m)
    return m

def save_and_view_map(f_map, output_file):
    f_map.save(f"{output_file}.html")
    webbrowser.open_new_tab(f"{output_file}.html")
    return 1

def main_function(table_name, s0801_file, s1902_file, segment_file, census_file, output_map_file):
    # Add census data to census tracts in geojson shapefile for Seattle
    print("Modifying and writing census data...")
    write_census_data_to_csv(s0801_file, s1902_file, census_file)

    # Connect to dynamodb
    print("Connecting to dynamodb...")
    table = connect_to_dynamo_table(table_name)

    # Query the dynamoDB for all speed data, in this case all speeds above 0
    print("Getting speed data from dynamodb...")
    speed_lookup = table_to_lookup(table)
    print("Writing speed data to segments for visualization...")
    speeds = write_speeds_to_map_segments(speed_lookup, segment_file)

    # Create the color mapping for speeds
    print("Generating map...")
    linear_cm = cm.LinearColormap(['red', 'green'], vmin=np.percentile(speeds, 1), vmax=np.percentile(speeds, 75))
    f_map = generate_folium_map(segment_file, census_file, linear_cm)
    print("Saving and opening map...")
    save_and_view_map(f_map, output_map_file)
    return 1