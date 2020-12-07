#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke_census(cls) -- smoke test for writing census data to geoJSON

test_oneshot_census(self) -- one-shot test for writing census data to geoJSON

test_smoke_folium_map(cls) -- smoke test for generating folium map

"""

import unittest

import branca.colormap as cm

from src import vis_functions

S0801_PATH = './data/s0801'
S1902_PATH = './data/s1902'
SEGMENT_FILE = './tests/kcm_routes_exploded_modified'
CENSUS_FILE = './tests/seattle_census_tracts_2010'
LINEAR_CM = cm.LinearColormap(['red', 'green'],\
                              vmin=0.5,\
                              vmax=100.)

class TestTransitVis(unittest.TestCase):
    """
    Unittest for the module 'vis_functions'
    """
    @classmethod
    def test_smoke_census(cls):
        """
        Smoke test for the function 'write_census_data_to_csv'
        """

        assert vis_functions.write_census_data_to_csv(S0801_PATH,\
                                                        S1902_PATH,\
                                                        CENSUS_FILE)\
                                                        is not None
    def test_oneshot_census(self):
        """
        One shot test for the function 'write_census_data_to_csv'
        """

        self.assertAlmostEqual(vis_functions.write_census_data_to_csv(\
                                                        S0801_PATH,\
                                                        S1902_PATH,\
                                                        CENSUS_FILE), 1)

    @classmethod
    def test_smoke_folium_map(cls):
        """
        Smoke test for the function 'generate_folium_map'
        """

        assert vis_functions.generate_folium_map(SEGMENT_FILE,\
                                                CENSUS_FILE,\
                                                LINEAR_CM) \
                                                is not None
                                                
    @classmethod
    def test_smoke_save_map(cls):
        """
        Smoke test for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(SEGMENT_FILE,\
                                                CENSUS_FILE,\
                                                LINEAR_CM)
        output_file = 'output_map'
        assert vis_functions.save_and_view_map(f_map, output_file) \
                                                is not None    
                                                
    def test_oneshot_save_map(self):
        """
        One-shot test for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(SEGMENT_FILE,\
                                                CENSUS_FILE,\
                                                LINEAR_CM)
        output_file = 'output_map'
        self.assertAlmostEqual(vis_functions.save_and_view_map(\
                                               f_map, output_file), 1)                                             
##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
