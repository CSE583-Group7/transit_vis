#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke(cls) -- smoke test

"""

import unittest

import branca.colormap as cm

from src import transit_vis


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
        tract_shapes_path = './data/seattle_census_tracts_2010'

        assert transit_vis.write_census_data_to_geojson(s0801_path,\
                                                        s1902_path,\
                                                        tract_shapes_path)\
                                                        is not None

    def test_smoke_folium_map(cls):
        """
        Smoke test for the module 'transit_vis'
        """
        
        segment_file = './data/kcm_routes_exploded_modified'
        census_file = './data/seattle_census_tracts_2010'
        linear_cm = cm.LinearColormap(['red', 'green'],\
                                      vmin=0.5,\
                                      vmax=100.)

        assert transit_vis.generate_folium_map(segment_file,\
                                               census_file, linear_cm) \
                                                        is not None                                                        
                                                        

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
