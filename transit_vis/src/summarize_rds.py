#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=E0611
# pylint: disable=E0401
"""Gathers the last 24hrs of speed data, aggregates it, and uploads it.

This module takes speeds from a SQL data-warehouse and summarizes them to then
upload to the dynamodb database which our visualization draws from. This is
a necessity because querying large (24hrs+) amounts of data from the warehouse
can take upwards of 10 minutes, rendering the tool slow and useless. This script
is run once per day to summarize the daily speeds to the segments created by the
initialize_dynamodb module, however it is also possible to do many days at once.
RAM must be managed carefully to avoid OOM errors, so for a 24hr query at least
3gb is recommended. If using less, the query time period should be split up
smaller than 24hrs.
"""


from datetime import datetime
from zipfile import ZipFile
import requests

import boto3
import numpy as np
import pandas as pd
import psycopg2

from transit_vis.src import config as cfg


def convert_cursor_to_tabular(query_result_cursor):
    """Converts a cursor returned by a SQL execution to a Pandas dataframe.

    First iterates through the cursor and dumps all of the contents into a numpy
    array for easier access. Then, a dataframe is created and grown to store the
    full contents of the cursor. This function's main purpose is to make the
    query results easier to work with in other functions. It may slow down the
    processing especially if extremely large (>24hrs) queries are made.

    Args:
        query_result_cursor: A Psycopg Cursor object pointing to the first
            result from a query for bus locations from the data warehouse. The
            results should contain columns for tripid, vehicleid, orientation,
            scheduledeviation, locationtime, and collectedtime.

    Returns:
        A Pandas Dataframe object containing the query results in tabular
        form.
    """
    # Pull out all the variables from the query result cursor and store in array
    all_tracks = []
    for record in query_result_cursor:
        track = []
        for feature in record:
            track = np.append(track, feature)
        all_tracks.append(track)

    # Convert variables integers, store in Pandas, and return
    daily_results = pd.DataFrame(all_tracks)
    colnames = []
    for col in query_result_cursor.description:
        colnames.append(col.name)
    daily_results.columns = colnames
    daily_results = daily_results.dropna()
    daily_results['tripid'] = daily_results['tripid'].astype(int)
    daily_results['vehicleid'] = daily_results['vehicleid'].astype(int)
    daily_results['orientation'] = daily_results['orientation'].astype(int)
    daily_results['scheduledeviation'] = daily_results['scheduledeviation'].astype(int)
    daily_results['locationtime'] = daily_results['locationtime'].astype(int)
    daily_results['collectedtime'] = daily_results['collectedtime'].astype(int)
    return daily_results

def connect_to_rds():
    """Connects to the RDS data warehouse specified in config.py.

    Attempts to connect to the database, and if successful it returns a
    connection object that can be used for queries to the bus location data.

    Returns:
        A Psycopg Connection object for the RDS data warehouse specified in
        config.py.
    """
    conn = psycopg2.connect(
        host=cfg.HOST,
        database=cfg.DATABASE,
        user=cfg.UID,
        password=cfg.PWD)
    return conn

def get_last_xdays_results(conn, num_days, rds_limit):
    """Queries the last x days worth of data from the RDS data warehouse.

    Uses the database connection to execute a query for the last x days of
    bus coordinates stored in the RDS data warehouse. The RDS data must have a
    column for collected time (in epoch format) which is used to determine the
    time. The query is made based on the current system time, so it will count
    x days back from the present on the current system. All time comparisons
    between the RDS and the system are done in epoch time, so there should be no
    concern for time zone differences if running this function from an EC2
    instance.

    Args:
        conn: A Psycopg Connection object for the RDS data warehouse.
        rds_limit: An integer specifying the maximum number of rows to query.
            Useful for debugging and checking output before making larger
            queries. Set to 0 for no limit.

    Returns:
        A Pandas Dataframe object containing the results in the database for the
        last x day period.
    """
    # Query the specified number of days back from current time
    end_time = round(datetime.now().timestamp())
    start_time = end_time - (24*60*60)
    i = 1
    while i < num_days:
        end_time = start_time
        start_time = end_time - (24*60*60)
        i += 1

    if rds_limit > 0:
        query_text = f"SELECT * FROM active_trips_study WHERE collectedtime " \
            f"BETWEEN {start_time} AND {end_time} LIMIT {rds_limit};"
    else:
        query_text = f"SELECT * FROM active_trips_study WHERE collectedtime " \
            f"BETWEEN {start_time} AND {end_time};"
    with conn.cursor() as curs:
        curs.execute(query_text)
        daily_results = convert_cursor_to_tabular(curs)
    return daily_results

def update_gtfs_route_info():
    """Downloads the latest trip-route conversions from the KCM GTFS feed.

    Connects to the King County Metro GTFS server and requests the latest GTFS
    files. Saves the files in .zip format and then extracts their content to a
    folder named 'google transit'. This will be used when assigning route ids to
    the bus coordinate data from RDS, so that they can then be aggregated to
    matching segments.

    Returns:
        1 when the download and unzipping process is complete.
    """
    url = 'http://metro.kingcounty.gov/GTFS/google_transit.zip'
    req = requests.get(url, allow_redirects=True)
    open('../data/google_transit.zip', 'wb').write(req.content)
    with ZipFile('../data/google_transit.zip', 'r') as zip_obj:
        zip_obj.extractall('../data/google_transit')
    return 1

def preprocess_trip_data(daily_results):
    """Cleans the tabular trip data and calculates average speed.

    Removes rows with duplicated tripid, locationid columns from the data. These
    rows are times where the OneBusAway API was queried faster than the bus
    location was updated, creating duplicate info. Buses update at around 30s
    intervals and the API is queried at 10s intervals so there is a large amount
    of duplicate data. Speeds are calculated between consecutive bus locations
    based on the distance traveled and the time between those locations. Speeds
    that are below 0 m/s, or above 30 m/s are assumed to be GPS multipathing or
    other recording errors and are removed.

    Args:
        daily_results: A Pandas Dataframe object containing bus location, time,
            and other RDS data.

    Returns:
        A Pandas Dataframe object containing the cleaned set of results with an
        additional column named 'avg_speed_m_s'.
    """
    # Remove duplicate trip locations
    daily_results.drop_duplicates(
        subset=['tripid', 'locationtime'], inplace=True)
    daily_results.sort_values(
        by=['tripid', 'locationtime'], inplace=True)

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
    daily_results.loc[:, 'dist_diff'] = daily_results['tripdistance'] \
        - daily_results['prev_tripdistance']
    daily_results.loc[:, 'time_diff'] = daily_results['locationtime'] \
        - daily_results['prev_locationtime']
    daily_results.loc[:, 'avg_speed_m_s'] = daily_results['dist_diff'] \
        / daily_results['time_diff']

    # Remove rows where speed is below 0 or above 30 and round
    daily_results = daily_results[daily_results['avg_speed_m_s'] >= 0]
    daily_results = daily_results[daily_results['avg_speed_m_s'] <= 30]
    daily_results.loc[:, 'avg_speed_m_s'] = round(
        daily_results.loc[:, 'avg_speed_m_s'])
    return daily_results

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

def upload_to_dynamo(dynamodb_table, to_upload):
    """Uploads the speeds gathered and processed from the RDS to dynamodb.

    Groups all bus speed observations by route/segment ids and averages the
    observed speeds. Uploads the results to dynamodb; replaces avg_speed_m_s
    with the latest value, and appends to historic_speeds which keeps track of
    past average daily speeds for each segment.

    Args:
        dynamodb_table: A boto3 Table pointing to a dynamodb table that has been
            initialized to contain the same segments as to_upload.
        to_upload: A Pandas Dataframe to be uploaded to dynamodb containing
            route ids, and their average speeds

    Returns:
        The length of the to_upload argument.
    """
    # Aggregate the observed bus speeds by their route/segment ids
    to_upload = to_upload[['route_id', 'trip_short_name', 'avg_speed_m_s']]
    to_upload = to_upload.groupby(['route_id', 'trip_short_name']).mean().reset_index()
    to_upload['avg_speed_m_s'] = round(to_upload['avg_speed_m_s'], 1)
    to_upload['avg_speed_m_s'] = to_upload['avg_speed_m_s'].apply(str)
    to_upload = to_upload.to_dict(orient='records')

    # Update each route/segment id in the dynamodb with its new value
    for track in to_upload:
        dynamodb_table.update_item(
            Key={
                'route_id': track['route_id'],
                'local_express_code': track['trip_short_name'][0]},
            UpdateExpression="SET avg_speed_m_s=:speed," \
                "historic_speeds=list_append(" \
                "if_not_exists(historic_speeds, :empty_list), :vals)",
            ExpressionAttributeValues={
                ':speed': track['avg_speed_m_s'],
                ':vals': [track['avg_speed_m_s']],
                ':empty_list': []})
    return len(to_upload)

def main_function(dynamodb_table_name, num_days, rds_limit):
    """Queries 24hrs of data from RDS, calculates speeds, and uploads them.

    Runs daily to take 24hrs worth of data stored in the data warehouse
    and summarize it for usage with the Folium map. Speeds for each observed
    bus location are calculated using consecutive trip distances and times.The
    geojson segments used are generated during initialize_dynamodb.py, which
    guarantees that they will be the same ones that are stored on the dynamodb
    database, allowing for this script to upload them. The Folium map will then
    download the speeds and display them using the same geojson file once again.

    Args:
        dynamodb_table_name: The name of the table containing the segments that
            speeds will be matched and uploaded to.
        num_days: How many days back data should be queried from RDS to be added
            to the dynamodb database. Helpful for quickly populating dynamodb
            with speeds when first setting it up. Set to 1 to use last 24hrs of
            data.
        rds_limit: An integer specifying the maximum number of rows to query.
            Useful for debugging and checking output before making larger
            queries. Set to 0 for no limit.

    Returns:
        An integer of the number of segments that were updated in the
        database.
    """
    # Update the current gtfs trip-route info from King County Metro
    print("Updating the GTFS files...")
    update_gtfs_route_info()

    # Load 24hrs of scraped data
    print("Connecting to RDS...")
    conn = connect_to_rds()
    print("Querying data from RDS (10-20mins if no limit specified)...")
    daily_results = get_last_xdays_results(conn, num_days, rds_limit)
    print("Finished query; processing RDS data...")
    daily_results = preprocess_trip_data(daily_results)

    # Load the gtfs trip-route info and segment shapefile
    print("Loading shapefile and GTFS files...")
    gtfs_trips = pd.read_csv('../data/google_transit/trips.txt')
    gtfs_trips = gtfs_trips[['route_id', 'trip_id', 'trip_short_name']]
    gtfs_routes = pd.read_csv('../data/google_transit/routes.txt')
    gtfs_routes = gtfs_routes[['route_id', 'route_short_name']]

    # Merge scraped data with the gtfs data and alter route ids to fit schema
    print("Merging RDS data with GTFS files...")
    daily_results = daily_results.merge(
        gtfs_trips,
        left_on='tripid',
        right_on='trip_id')
    daily_results = daily_results.merge(
        gtfs_routes,
        left_on='route_id',
        right_on='route_id')

    # Upload to dynamoDB
    print("Uploading aggregated segment data to dynamoDB...")
    table = connect_to_dynamo_table(dynamodb_table_name)
    success = upload_to_dynamo(table, daily_results)
    return success

if __name__ == "__main__":
    NUM_SEGMENTS_UPDATED = main_function(
        dynamodb_table_name='KCM_Bus_Routes',
        num_days=1,
        rds_limit=10000)
    print(f"Number of segments updated: {NUM_SEGMENTS_UPDATED}")
