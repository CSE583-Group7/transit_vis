from datetime import datetime
import decimal
import json
import requests
from zipfile import ZipFile

import boto3
import numpy as np
import psycopg2
import pandas as pd
from sklearn.neighbors import BallTree

import config as cfg

def convert_cursor_to_tabular(query_result_cursor):
    # Pull out the variables from the query result cursor
    all_tracks = []
    for record in query_result_cursor:
        track = []
        for feature in record:
            track = np.append(track, feature)
        all_tracks.append(track)
        
    # Convert variables to Pandas and return
    daily_results = pd.DataFrame(all_tracks)
    colnames = []
    for col in query_result_cursor.description:
        colnames.append(col.name)
    daily_results.columns = colnames
    daily_results['tripid'] = daily_results['tripid'].astype(int)
    daily_results['vehicleid'] = daily_results['vehicleid'].astype(int)
    daily_results['orientation'] = daily_results['orientation'].astype(int)
    daily_results['scheduledeviation'] = daily_results['scheduledeviation'].astype(int)
    daily_results['locationtime'] = daily_results['locationtime'].astype(int)
    daily_results['collectedtime'] = daily_results['collectedtime'].astype(int)
    return daily_results

def load_modified_geojson(path_to_geojson):
    with open(path_to_geojson, 'r') as f:
        kcm_routes = json.load(f)
    return kcm_routes

def connect_to_rds():
    try:
        conn = psycopg2.connect(
        host=cfg.HOST,
        database=cfg.DATABASE,
        user=cfg.UID,
        password=cfg.PWD)
    except:
        pass
    return conn

def get_last_24hrs_results(conn, rds_limit):
    # Query the last 24 hours of data from the RDS database
    end_time = round(datetime.now().timestamp())
    start_time = end_time - (24*60*60)
    if rds_limit > 0:
        query_text = f"SELECT * FROM active_trips_study WHERE collectedtime BETWEEN {start_time} AND {end_time} LIMIT {rds_limit};"
    else:
        query_text = f"SELECT * FROM active_trips_study WHERE collectedtime BETWEEN {start_time} AND {end_time};"
    with conn.cursor() as curs:
        curs.execute(query_text)
        daily_results = convert_cursor_to_tabular(curs)
    return daily_results
    
def update_gtfs_route_info():
    # Get the latest GTFS route - trip data from the KCM FTP server
    url = 'http://metro.kingcounty.gov/GTFS/google_transit.zip'
    r = requests.get(url, allow_redirects=True)
    open('../data/google_transit.zip', 'wb').write(r.content)
    with ZipFile('../data/google_transit.zip', 'r') as zipObj:
        zipObj.extractall('../data/google_transit')
    return 1

def preprocess_trip_data(daily_results):
    # Remove duplicate trip locations
    daily_results.drop_duplicates(subset=['tripid','locationtime'], inplace=True)
    daily_results.sort_values(by=['tripid','locationtime'], inplace=True)

    # Offset tripdistance, locationtime, and tripids by 1
    daily_results['prev_tripdistance'] = 1
    daily_results['prev_locationtime'] = 1
    daily_results['prev_tripid'] = 1
    daily_results['prev_tripdistance'] = daily_results['tripdistance'].shift(1)
    daily_results['prev_locationtime'] = daily_results['locationtime'].shift(1)
    daily_results['prev_tripid'] = daily_results['tripid'].shift(1)

    # Remove NA rows, and rows where tripid is different (last recorded location)
    daily_results.loc[daily_results.tripid == daily_results.prev_tripid, 'tripid'] = None
    daily_results.dropna(inplace=True)
    
    # Calculate average speed between each location bus is tracked at
    daily_results.loc[:,'dist_diff'] = daily_results['tripdistance'] - daily_results['prev_tripdistance']
    daily_results.loc[:,'time_diff'] = daily_results['locationtime'] - daily_results['prev_locationtime']
    daily_results.loc[:,'avg_speed_m_s'] = daily_results['dist_diff'] / daily_results['time_diff']

    # Remove rows where speed is below 0 or above 30 and round to one decimal place
    daily_results = daily_results[daily_results['avg_speed_m_s'] >= 0]
    daily_results = daily_results[daily_results['avg_speed_m_s'] <= 30]
    daily_results.loc[:,'avg_speed_m_s'] = round(daily_results.loc[:,'avg_speed_m_s'])
    return daily_results

def route_ids_to_keys(daily_results):
    # Concat 1 or 0 to the route id to make it fit with dynamoDB key schema
    daily_results.loc[daily_results['trip_short_name']=='LOCAL', 'route_id'] = daily_results['route_id'].apply(lambda x:
                                                                                                               int(str(x) + '0'))
    daily_results.loc[daily_results['trip_short_name']=='EXPRESS', 'route_id'] = daily_results['route_id'].apply(lambda x:
                                                                                                                 int(str(x) + '1'))
    return daily_results

def get_nearest(src_points, candidates, k_neighbors=1):
    """Find nearest neighbors for all source points from a set of candidate points"""

    # Create tree from the candidate points
    tree = BallTree(candidates, leaf_size=15, metric='haversine')

    # Find closest points and distances
    distances, indices = tree.query(src_points, k=k_neighbors)

    # Transpose to get distances and indices into arrays
    distances = distances.transpose()
    indices = indices.transpose()

    # Get closest indices and distances (i.e. array at index 0)
    # note: for the second closest points, you would take index 1, etc.
    closest_idx = indices[0]
    closest_dist = distances[0]
    return (closest_idx, closest_dist)

def assign_results_to_segments(kcm_routes, daily_results):
    # Convert segment data from json format to tabular, so that it can be used with nearest neighbors function
    feature_coords = []
    route_ids = []
    seg_ids = []
    for feature in kcm_routes['features']:
        for coord_pair in feature['geometry']['coordinates']:
            feature_coords.append(coord_pair)
            route_ids.append(feature['route_id'])
            seg_ids.append(feature['segment_id'])
    segments = pd.DataFrame()
    segments['route_id'] = route_ids
    segments['segment_id'] = seg_ids
    segments['lat'] = np.array(feature_coords)[:,0]
    segments['lon'] = np.array(feature_coords)[:,1]
    
    # Go route by route, adding all data points collected from the database to their closest segment that shares their route_id
    to_upload = pd.DataFrame()
    route_list = pd.unique(daily_results['route_id'])
    for route in route_list:
        route_results = daily_results[daily_results['route_id']==route]
        route_segments = segments[segments['route_id']==route].reset_index()

        # Use closest index returned by get_nearest to join the closest segment info back to each datapoint
        if len(route_results) > 0 and len(route_segments) > 0:
            result_idxs, result_dists = get_nearest(route_results[['lat', 'lon']], route_segments[['lat', 'lon']])
            route_results = route_results.reset_index().join(route_segments.loc[result_idxs,:].reset_index(), rsuffix='_seg')
            to_upload = to_upload.append(route_results)
        else:
            # A route was tracked by OneBusAway that does not have an id in the King County Metro shapefile
            print(f"Route {route} was either not tracked, or does not have an id in the KCM shapefile")
            result_idxs = -1
            result_dists = -1
    return to_upload

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

def upload_to_dynamo(dynamodb_table, to_upload):
    # Summarize the bus delay data (for now, just get the average speed for the day per segment)
    to_upload = to_upload[['route_id', 'segment_id', 'avg_speed_m_s']]
    to_upload = to_upload.groupby(['route_id', 'segment_id']).mean().reset_index()
    to_upload['avg_speed_m_s'] = round(to_upload['avg_speed_m_s'], 1)
    to_upload['avg_speed_m_s'] = to_upload['avg_speed_m_s'].apply(str)
    to_upload = to_upload.to_dict(orient='records')

    # Update each route/segment combination with its avg speed for the day
    for track in to_upload:
        response = dynamodb_table.update_item(
            Key={
                'route_id': track['route_id'],
                'segment_id': track['segment_id']
            },
            UpdateExpression="SET avg_speed_m_s=:speed, historic_speeds=list_append(if_not_exists(historic_speeds, :empty_list), :vals)",
            ExpressionAttributeValues={
                ':speed': track['avg_speed_m_s'],
                ':vals': [track['avg_speed_m_s']],
                ':empty_list': []
            })
    return len(to_upload)
    
def main_function(dynamodb_table_name, rds_limit):
    # Update the current gtfs trip-route info from the King County Metro FTP server
    print("Updating the GTFS files...")
    update_gtfs_route_info()

    # Load last 24hrs of scraped data
    print("Connecting to RDS...")
    conn = connect_to_rds()
    print("Querying the last 24 hours of data from RDS (10-20mins)...")
    daily_results = get_last_24hrs_results(conn, rds_limit)
    print("Finished query; processing RDS data...")
    daily_results = preprocess_trip_data(daily_results)
    
    # Load the gtfs trip-route info and segment shapefile
    print("Loading shapefile and GTFS files...")
    gtfs_trips = pd.read_csv('../data/google_transit/trips.txt')
    gtfs_trips = gtfs_trips[['route_id', 'trip_id', 'trip_short_name']]
    kcm_routes = load_modified_geojson('../data/kcm_routes_exploded_modified.geojson')

    # Merge scraped data with the gtfs data to assign route_ids to the scraped data, then update route_id to fit dynamodb key schema
    print("Merging RDS data with GTFS files...")
    daily_results = daily_results.merge(gtfs_trips, left_on='tripid', right_on='trip_id')
    daily_results = route_ids_to_keys(daily_results)
    
    # Match the scraped data to its closest segments in the route shapefile
    print("Matching RDS data to nearest segments in shapefile...")
    daily_results = assign_results_to_segments(kcm_routes, daily_results)

    # Summarize the last 24 hours of bus movement data, and upload to dynamoDB
    print("Uploading aggregated segment data to dynamoDB...")
    table = connect_to_dynamo_table(dynamodb_table_name)
    success = upload_to_dynamo(table, daily_results)
    return success

num_segments_updated = main_function('KCM_Bus_Routes_Modified_Production', 0)
print(f"Number of segments updated: {num_segments_updated}")
