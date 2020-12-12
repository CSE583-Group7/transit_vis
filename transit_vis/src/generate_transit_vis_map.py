import transit_vis_streets

transit_vis_streets.main_function(table_name='KCM_Bus_Routes',
              s0801_file='../data/s0801',
              s1902_file='../data/s1902',
              segment_file='../data/kcm_routes', 
              census_file='../data/seattle_census_tracts_2010', 
              output_map_file='output_map')