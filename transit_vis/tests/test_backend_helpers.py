#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test helper functions for the repository 'transit_vis'

test_smoke_floats(cls) -- smoke test for replacing nested floats with strs

test_oneshot_floats(self) -- oneshot test for replacing nested floats with strs

test_smoke_gtfs(cls) -- smoke test for updating the gtfs data source

test_oneshot_gtfs(self) -- oneshot test for updating the gtfs data source
"""


import os

import unittest
import numpy as np
import pandas as pd

from transit_vis.src import initialize_dynamodb
from transit_vis.src import summarize_rds


#replace floats and update gtfs
DATA_PATH = './transit_vis/data'
nested_list = [1.1, 2.2, 3.3, [4.4, 5.5, 6.1]]
daily_results = pd.read_csv("transit_vis/tests/data/daily_results_test.csv")

class TestBackendHelpers(unittest.TestCase):
    """
    Unittest for helper functions in 'initialize_dynamodb' and 'summarize_rds'
    """
    @classmethod
    def test_smoke_floats(cls):
        """
        Smoke test for the function 'replace_floats'
        """
        assert initialize_dynamodb.replace_floats(nested_list) is not None

    def test_oneshot_floats(self):
        """
        One shot test for the function 'replace_floats'
        """
        stringed_list = initialize_dynamodb.replace_floats(nested_list)
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
        to_upload = np.array([1,1])
        dynamodb_table = np.array([1,1])

        try:
             summarize_rds.upload_to_dynamo(dynamodb_table, to_upload)
        except TypeError:
            pass

    @classmethod
    def test_edgecase_get_results(cls):
        """
        Edge case test to catch pandas dataframe is not inputted to
        'upload_to_dynamo'
        """
        conn = None
        num_days = 7
        rds_limit = '1'
        try:
             summarize_rds.get_last_xdays_results(conn, num_days, rds_limit)
        except TypeError:
            pass

    @classmethod
    def test_edgecase_get_results_negative(cls):
        """
        Edge case test to catch pandas dataframe is not inputted to
        'upload_to_dynamo'
        """
        conn = None
        num_days = 7
        rds_limit = -1

        try:
             summarize_rds.get_last_xdays_results(conn, num_days, rds_limit)
        except TypeError:
            pass

    @classmethod
    def test_smoke_preprocess(cls):
        """
        Smoke test for the function 'preprocess_trip_data'
        """
        assert summarize_rds.preprocess_trip_data(daily_results) is not None

    def test_oneshot_preprocess(self):
        """
        Oneshot test for the function 'preprocess_trip_data'
        """
        x = summarize_rds.preprocess_trip_data(daily_results)
        self.assertTrue(pd.notnull(x).any)

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestBackendHelpers)
_ = unittest.TextTestRunner().run(SUITE)
