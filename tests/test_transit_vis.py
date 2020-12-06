#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Class to test the repository 'transit_vis'

test_smoke(cls) -- smoke test

"""

import unittest

from src import transit_vis


class TestTransitVis(unittest.TestCase):
    """
    Unittest for the module 'transit_vis'
    """
    @classmethod
    def test_smoke(cls):
        """
        Smoke test for the module 'transit_vis'
        """

        assert transit_vis.main_function('KCM_Bus_Routes_Modified_Production',
             './data/s0801',
             './data/s1902',
             './data/kcm_routes_exploded_modified', 
             './data/seattle_census_tracts_2010', 
             'output_map') is not None

##############################################################################

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTransitVis)
_ = unittest.TextTestRunner().run(SUITE)
