# pylint: disable=E1101
"""Run the main function to compile and generate the final visualization html

This is the script that executes "main_function" within the module
"transit_vis" that brings together all the other analysis functions. The
inputs include the main data as well as the ancillary data to aid in
performing the analysis. The census data is also inputted to
provide supplementary data to the final map.
"""


import transit_vis


# Generate and show map
transit_vis.main_function(table_name='KCM_Bus_Routes',\
                         s0801_path='../data/s0801',\
                         s1902_path='../data/s1902',\
                         segment_path='../data/kcm_routes',\
                         census_path='../data/seattle_census_tracts_2010')
