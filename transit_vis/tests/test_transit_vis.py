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


import os
import unittest

import branca.colormap as cm
import numpy as np

from transit_vis.src import transit_vis as vis_functions


S0801_PATH = './transit_vis/tests/data/s0801'
S1902_PATH = './transit_vis/tests/data/s1902'
SEGMENT_PATH = './transit_vis/tests/data/kcm_routes'
CENSUS_PATH = './transit_vis/tests/data/seattle_census_tracts_2010'
OUTPUT_PATH = './transit_vis/tests/output_map.html'
LINEAR_CM = cm.LinearColormap(['red', 'green'], vmin=0.5, vmax=100.)
ROUTE_DICT = {}
ROUTE_DICT[(100001, 'L')] = {'avg_speed_m_s': 7.5, 'historic_speeds': [2.2, 7.5]}
ROUTE_DICT[(999999, 'L')] = {'avg_speed_m_s': 5.9, 'historic_speeds': [0.5, 5.9]}


class TestTransitVis(unittest.TestCase):
    """
    Unittest for the module 'vis_functions'
    """
    @classmethod
    def test_smoke_census(cls):
        """
        Smoke test for the function 'write_census_data_to_csv'
        """
        assert vis_functions.write_census_data_to_csv(
            S0801_PATH,
            S1902_PATH,
            CENSUS_PATH) is not None

    def test_oneshot_census(self):
        """
        One shot test for the function 'write_census_data_to_csv'
        """
        if os.path.exists(f"{CENSUS_PATH}_tmp.csv"):
            os.remove(f"{CENSUS_PATH}_tmp.csv")
        vis_functions.write_census_data_to_csv(
            S0801_PATH,
            S1902_PATH,
            CENSUS_PATH)
        self.assertTrue(os.path.exists(f"{CENSUS_PATH}_tmp.csv"))

    @classmethod
    def test_smoke_folium_map(cls):
        """
        Smoke test for the function 'generate_folium_map'
        """
        assert vis_functions.generate_folium_map(
            SEGMENT_PATH,
            CENSUS_PATH,
            LINEAR_CM) is not None

    @classmethod
    def test_smoke_write_speed(cls):
        """
        Smoke test for the function 'write_speeds_to_map_segments'
        """
        speed_lookup = ROUTE_DICT
        assert vis_functions.write_speeds_to_map_segments(
            speed_lookup,
            SEGMENT_PATH) is not None

    def test_oneshot_write_speed(self):
        """
        One-shot test for the function 'write_speeds_to_map_segments'
        """
        speed_lookup = ROUTE_DICT
        speeds_test = vis_functions.write_speeds_to_map_segments(
            speed_lookup,
            SEGMENT_PATH)
        self.assertTrue(np.array_equal(speeds_test, [7.5]))

    def test_edgecase_write_speed(self):
        """
        Edge case test to catch that speed inputs must be a dictionary and
        not an array for the function 'write_speeds_to_map_segments'
        """
        speed_lookup = np.array([1.0])
        with self.assertRaises(TypeError):
            vis_functions.write_speeds_to_map_segments(
                speed_lookup,
                SEGMENT_PATH)

    @classmethod
    def test_smoke_save_map(cls):
        """
        Smoke test for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(
            SEGMENT_PATH,
            CENSUS_PATH,
            LINEAR_CM)
        assert vis_functions.save_and_view_map(f_map, OUTPUT_PATH) is not None

    def test_oneshot_save_map(self):
        """
        One-shot test for the function 'save_and_view_map'
        """
        if os.path.exists('transit_vis/tests/output_map.html'):
            os.remove('transit_vis/tests/output_map.html')
        f_map = vis_functions.generate_folium_map(
            SEGMENT_PATH,
            CENSUS_PATH,
            LINEAR_CM)
        vis_functions.save_and_view_map(f_map, OUTPUT_PATH)
        self.assertTrue(os.path.exists(OUTPUT_PATH))

    def test_edgecase_save_map(self):
        """
        Edge case test to catch that file types other than html can not be
        used as the output file for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(
            SEGMENT_PATH,
            CENSUS_PATH,
            LINEAR_CM)
        bad_output_path = 'transit_vis/tests/output_map.csv'
        with self.assertRaises(ValueError):
            vis_functions.save_and_view_map(f_map, bad_output_path)

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
