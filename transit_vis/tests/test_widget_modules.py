#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke_census(cls) -- smoke test for writing census data to geoJSON

test_oneshot_census(self) -- one-shot test for writing census data to geoJSON

test_smoke_folium_map(cls) -- smoke test for generating folium map

test_smoke_write_speed(cls) -- smoke test for writing speeds to map

test_oneshot_write_speed(self) -- one shot test for writing speeds to map

test_edgecase_write_speed(cls) -- edge case to catch invalid input type

test_smoke_save_map(cls) -- smoke test for saving final map object

test_oneshot_save_map(self) -- one shot test for saving final map object

test_edgecase_save_map(cls) -- edge case to catch invalid file type to save to
"""


import unittest

import branca.colormap as cm

from transit_vis.src import widget_modules

S0801_PATH = './transit_vis/tests/data/s0801'
S1902_PATH = './transit_vis/tests/data/s1902'
SEGMENT_PATH = './transit_vis/tests/data/kcm_routes'
CENSUS_PATH = './transit_vis/tests/data/seattle_census_tracts_2010'
OUTPUT_PATH = './transit_vis/tests/output_map.html'
LINEAR_CM = cm.LinearColormap(['red', 'green'], vmin=0.5, vmax=100.)

HOME_LOC_VALUE = '47.653834, -122.307858'
DESTINATION_LOC_VALUE = '47.606209, -122.332069'
MIN_INCOME_VALUE = 30000
MAX_INCOME_VALUE = 60000

class TestWidgetModules(unittest.TestCase):
    """
    Unittest for the module 'vis_functions'
    """
    @classmethod
    def test_smoke_folium_map(cls):
        """
        Smoke test for the function 'generate_folium_map'
        """

        assert widget_modules.generate_folium_map_widget(
            SEGMENT_PATH, CENSUS_PATH, LINEAR_CM, HOME_LOC_VALUE, \
            DESTINATION_LOC_VALUE, MIN_INCOME_VALUE, \
            MAX_INCOME_VALUE) is not None


##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestWidgetModules)
_ = unittest.TextTestRunner().run(SUITE)