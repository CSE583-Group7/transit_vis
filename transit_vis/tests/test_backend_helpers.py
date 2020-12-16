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

from transit_vis.src import initialize_dynamodb
from transit_vis.src import summarize_rds


#replace floats and update gtfs
DATA_PATH = './transit_vis/data'
nested_list = [1.1, 2.2, 3.3, [4.4, 5.5, 6.1]]

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

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestBackendHelpers)
_ = unittest.TextTestRunner().run(SUITE)
