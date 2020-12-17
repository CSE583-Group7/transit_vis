#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test helper functions for the repository 'transit_vis'

test_smoke_floats(cls) -- smoke test for replacing nested floats with strs

test_smoke_floats_dict(cls) -- smoke test for replacing dictionary entries with strs

test_oneshot_floats(self) -- oneshot test for replacing nested floats with strs

test_smoke_gtfs(cls) -- smoke test for updating the gtfs data source

test_oneshot_gtfs(self) -- oneshot test for updating the gtfs data source

test_edgecase_upload(cls) -- edge case test input type for upload to dynamodb

test_edgecase_get_results(cls) -- edge case test for input type to get results

test_edgecase_get_results_negative(cls) -- edge case test for input value to get results

test_edgecase_get_results_no_connection(cls) -- edge case test for input value to get results

test_smoke_preprocess(cls) -- smoke test for preprocessing trip data

test_oneshot_preprocess(self) -- oneshot test for preprocessing trip data
"""


import os

import unittest
import numpy as np
import pandas as pd

from transit_vis.src import initialize_dynamodb
from transit_vis.src import summarize_rds


#replace floats and update gtfs
DATA_PATH = './transit_vis/data'
NESTED_LIST = [1.1, 2.2, 3.3, [4.4, 5.5, 6.1]]
NESTED_DICTIONARY = {'var1': 0.5, 'var2': 5.2}
DAILY_RESULTS = pd.read_csv("transit_vis/tests/data/daily_results_test.csv")
TO_UPLOAD = np.array([1, 1])
DYNAMODB_TABLE = np.array([1, 1])
CONN = None
NUM_DAYS = 7
RDS_LIMIT = 0

class TestBackendHelpers(unittest.TestCase):
    """
    Unittest for helper functions in 'initialize_dynamodb' and 'summarize_rds'
    """
    @classmethod
    def test_smoke_floats(cls):
        """
        Smoke test for the function 'replace_floats' with a list
        """
        assert initialize_dynamodb.replace_floats(NESTED_LIST) is not None

    @classmethod
    def test_smoke_floats_dict(cls):
        """
        Smoke test for the function 'replace_floats' with a dictionary
        """
        assert initialize_dynamodb.replace_floats(NESTED_DICTIONARY) is not None

    def test_oneshot_floats(self):
        """
        One shot test for the function 'replace_floats'
        """
        stringed_list = initialize_dynamodb.replace_floats(NESTED_LIST)
        for item in stringed_list:
            for subitem in item:
                self.assertFalse(isinstance(subitem, float))

    @classmethod
    def test_smoke_gtfs(cls):
        """
        Smoke test for the function 'update_gtfs_route_info'
        """
        assert summarize_rds.update_gtfs_route_info() is not None

    def test_oneshot_gtfs(self):
        """
        One shot test for the function 'update_gtfs_route_info'
        """
        if os.path.exists(f"{DATA_PATH}/google_transit.zip"):
            os.remove(f"{DATA_PATH}/google_transit.zip")
        summarize_rds.update_gtfs_route_info()
        self.assertTrue(os.path.exists(f"{DATA_PATH}/google_transit.zip"))

    @classmethod
    def test_edgecase_upload(cls):
        """
        Edge case test to catch pandas dataframe is not inputted to
        'upload_to_dynamo'
        """
        try:
            summarize_rds.upload_to_dynamo(DYNAMODB_TABLE, TO_UPLOAD)
        except TypeError:
            pass

    @classmethod
    def test_edgecase_get_results(cls):
        """
        Edge case test to catch bad type for rds limit inputted into
        'get_last_xdays_results'
        """
        bad_rds_limit = '1'
        try:
            summarize_rds.get_last_xdays_results(CONN, NUM_DAYS, bad_rds_limit)
        except TypeError:
            pass

    @classmethod
    def test_edgecase_get_results_negative(cls):
        """
        Edge case test to catch bad value for rds limit inputted into
        'get_last_xdays_results'
        """
        bad_rds_limit = -1

        try:
            summarize_rds.get_last_xdays_results(CONN, NUM_DAYS, bad_rds_limit)
        except ValueError:
            pass

    @classmethod
    def test_edgecase_get_results_no_connection(cls):
        """
        Edge case test to catch no Psycopg connection 'get_last_xdays_results'
        """
        try:
            summarize_rds.get_last_xdays_results(CONN, NUM_DAYS, RDS_LIMIT)
        except TypeError:
            pass

    @classmethod
    def test_smoke_preprocess(cls):
        """
        Smoke test for the function 'preprocess_trip_data'
        """
        assert summarize_rds.preprocess_trip_data(DAILY_RESULTS) is not None

    def test_oneshot_preprocess(self):
        """
        Oneshot test for the function 'preprocess_trip_data'
        """
        preprocessed_data = summarize_rds.preprocess_trip_data(DAILY_RESULTS)
        self.assertTrue(pd.notnull(preprocessed_data).any)

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestBackendHelpers)
_ = unittest.TextTestRunner().run(SUITE)
