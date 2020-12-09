from collections import defaultdict
import webbrowser

import boto3
from boto3.dynamodb.conditions import Key, Attr
import branca.colormap as cm
import folium
import json
import numpy as np
import pandas as pd

import config as cfg
import transit_vis

transit_vis.main_function('KCM_Bus_Routes_Modified_Production',
              '../data/s0801',
              '../data/s1902',
              '../data/kcm_routes_exploded_modified', 
              '../data/seattle_census_tracts_2010', 
              'output_map')