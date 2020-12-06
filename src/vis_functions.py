import webbrowser

import folium
import pandas as pd


def write_census_data_to_geojson(s0801_path, s1902_path, tract_shapes_path):
    # Read in the two tables that were taken from the ACS data portal website
    s0801_df = pd.read_csv(f"{s0801_path}.csv")
    s1902_df = pd.read_csv(f"{s1902_path}.csv")
    # Filter each table to only variables we are interested in, rename columns to be more descriptive
    commuters_df = s0801_df[['GEO_ID', 'NAME', 'S0801_C01_001E', 'S0801_C01_009E']]
    commuters_df.columns = ['GEO_ID', 'NAME', 'total_workers', 'workers_using_transit']
    commuters_df = commuters_df.loc[1:len(commuters_df),:]
    commuters_df['GEO_ID'] = commuters_df['GEO_ID'].str[-11:]
    households_df = s1902_df[['GEO_ID', 'NAME', 'S1902_C01_001E', 'S1902_C03_001E', 'S1902_C02_008E', 'S1902_C02_020E', 'S1902_C02_021E']]
    households_df.columns = ['GEO_ID', 'NAME', 'total_households', 'mean_income', 'percent_w_assistance', 'percent_white', 'percent_black_or_african_american']
    households_df = households_df.loc[1:len(households_df),:]
    households_df['GEO_ID'] = households_df['GEO_ID'].str[-11:]
    # Combine datasets on their census tract ID and write to .csv file for the visualization
    final_df = pd.merge(commuters_df, households_df, on='GEO_ID').drop(columns=['NAME_x', 'NAME_y'])
    final_df.to_csv(f"{tract_shapes_path}_tmp.csv", index=False)
    return 1


def generate_folium_map(segment_file, census_file, colormap):
    # Read in route shapefile and give it the style function above
    kcm_routes = folium.GeoJson(f"{segment_file}_w_speeds_tmp.geojson",
                                style_function=lambda feature: {
                                    'color': colormap(feature['properties']['AVG_SPEED_M_S']),
                                    'weight': 2}
                                )
    # Read in the census data/shapefile and create a choropleth based on income
    seattle_tracts_df = pd.read_csv(f"{census_file}_tmp.csv")
    seattle_tracts_df['GEO_ID'] = seattle_tracts_df['GEO_ID'].astype(str)
    seattle_tracts_df['mean_income'] = pd.to_numeric(seattle_tracts_df['mean_income'], errors='coerce')
    seattle_tracts_df = seattle_tracts_df.dropna()
    seattle_tracts = folium.Choropleth(geo_data=f"{census_file}.geojson",
                                    name='Socioeconomic Data',
                                    data=seattle_tracts_df,
                                    columns=['GEO_ID', 'mean_income'],
                                    key_on='feature.properties.GEOID10',
                                    fill_color='PuBu',
                                    fill_opacity=0.7,
                                    line_opacity=0.4,
                                    legend_name='mean income'
                                    )
    # Draw map using the updated kcm_routes with avg speed data and choropleth from census data
    m = folium.Map(location=[47.606209, -122.332069],
                zoom_start=11,
                prefer_canvas=True
                )
    seattle_tracts.add_to(m)
    kcm_routes.add_to(m)
    colormap.caption = 'Average Speed (m/s)'
    colormap.add_to(m)
    folium.LayerControl().add_to(m)
    return m

def save_and_view_map(f_map, output_file):
    f_map.save(f"{output_file}.html")
    webbrowser.open_new_tab(f"{output_file}.html")
    return 1