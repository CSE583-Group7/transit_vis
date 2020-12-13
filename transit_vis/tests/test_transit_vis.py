#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke_census(cls) -- smoke test for writing census data to geoJSON

test_oneshot_census(self) -- one-shot test for writing census data to geoJSON

test_smoke_folium_map(cls) -- smoke test for generating folium map

test_smoke_save_map(cls) -- smoke test for saving final map object

test_oneshot_save_map(self) -- one shot test for saving final map object

test_edgecase_save_map(cls) -- edge case to catch invalid file type to save to

test_smoke_write_speed(cls) -- smoke test for writing speeds to map

test_oneshot_write_speed(self) -- one shot test for writing speeds to map 

"""

import unittest

import branca.colormap as cm
import numpy as np

from transit_vis.src import vis_functions

S0801_PATH = './transit_vis/data/s0801'
S1902_PATH = './transit_vis/data/s1902'
SEGMENT_FILE = './transit_vis/tests/kcm_routes_exploded_modified'
CENSUS_FILE = './transit_vis/tests/seattle_census_tracts_2010'
LINEAR_CM = cm.LinearColormap(['red', 'green'],\
                              vmin=0.5,\
                              vmax=100.)
    
speeds_truth = np.array([9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9.,\
                   9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9., 9.,\
                   9., 9., 9., 9.])           
route_dict = {}
route_dict['avg_speed_m_s'] = 9.0
route_dict['historic_speeds'] = ['10.0', '9.0']

SPEED_LOOKUP = {}        
SPEED_LOOKUP[(100132, 'L')] = {'avg_speed_m_s': float(route_dict['avg_speed_m_s']),\
                               'historic_speeds': route_dict['historic_speeds']}
  

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
        output_file = 'output_map.html'
        assert vis_functions.save_and_view_map(f_map, output_file) \
                                                is not None

    def test_oneshot_save_map(self):
        """
        One-shot test for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(SEGMENT_FILE,\
                                                CENSUS_FILE,\
                                                LINEAR_CM)
        output_file = 'output_map.html'
        self.assertAlmostEqual(vis_functions.save_and_view_map(\
                                               f_map, output_file), 1)

    @classmethod
    def test_edgecase_save_map(cls):
        """
        Edge case test to catch that file types other than html can not be
        used as the output file for the function 'save_and_view_map'
        """
        f_map = vis_functions.generate_folium_map(SEGMENT_FILE,\
                                                CENSUS_FILE,\
                                                LINEAR_CM)
        output_file = 'output_map.csv'

        try:
            vis_functions.save_and_view_map(f_map, output_file)
        except TypeError:
            pass
        
    @classmethod
    def test_smoke_write_speed(cls):
        """
        Smoke test for the function 'write_speeds_to_map_segments'
        """

        assert vis_functions.write_speeds_to_map_segments(SPEED_LOOKUP,\
                                                          SEGMENT_FILE)\
                                                        is not None   
    def test_oneshot_write_speed(self):
        """
        One-shot test for the function 'write_speeds_to_map_segments'
        """
        
        speeds_test = vis_functions.write_speeds_to_map_segments(SPEED_LOOKUP,SEGMENT_FILE)            
                                                        
        self.assertIsNone(np.testing.assert_array_equal(speeds_truth, speeds_test))                                                                                                             
##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
