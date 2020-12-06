#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke(cls) -- smoke test

"""

import unittest

import branca.colormap as cm

from src import vis_functions


class TestTransitVis(unittest.TestCase):
    """
    Unittest for the module 'transit_vis'
    """
    @classmethod
    def test_smoke_census(cls):
        """
        Smoke test for the function 'write_census_data_to_geojson'
        """
        s0801_path = './data/s0801'
        s1902_path = './data/s1902'
        tract_shapes_path = './tests/seattle_census_tracts_2010'

        assert vis_functions.write_census_data_to_geojson(s0801_path,\
                                                        s1902_path,\
                                                        tract_shapes_path)\
                                                        is not None

    def test_smoke_folium_map(cls):
        """
        Smoke test for the module 'transit_vis'
        """
        
        segment_file = './tests/kcm_routes_exploded_modified'
        census_file = './tests/seattle_census_tracts_2010'
        linear_cm = cm.LinearColormap(['red', 'green'],\
                                      vmin=0.5,\
                                      vmax=100.)

        assert vis_functions.generate_folium_map(segment_file,\
                                               census_file, linear_cm) \
                                                        is not None                                                        
                                                        
    def test_save_and_view_map(cls):
        """
        Smoke test for the module 'save_and_view_map'
        """
        
        segment_file = './tests/kcm_routes_exploded_modified'
        census_file = './tests/seattle_census_tracts_2010'
        linear_cm = cm.LinearColormap(['red', 'green'],\
                                      vmin=0.5,\
                                      vmax=100.)
            
        f_map = vis_functions.generate_folium_map(segment_file,census_file, linear_cm)
        output_map_file = 'output_map' 

        assert vis_functions.save_and_view_map(f_map, output_map_file) \
                                                        is not None                                                          

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
