"""Set up and run transit_vis with a widget interface for a jupyter notebook

This sets up the widget interface and then collects the inputs to integrate
with the transit_vis data visualization
"""

from ipywidgets import VBox, Layout, widgets
from IPython.display import display, clear_output

import folium
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import branca.colormap as cm
import transit_vis.src.transit_vis as transit_vis

# Generates folium map based off census data, transportation data, and user inputs
def generate_folium_map_widget(segment_file, census_file, colormap,\
                               home_loc_value, destination_loc_value, \
                                   min_income_value, max_income_value):
    """Draws together speed/socioeconomic data to create a Folium map.

    Loads segments with speed data, combined census data, and the colormap
    generated from the list of speeds to be plotted. Plots all data sources on
    a new Folium Map object centered on Seattle, and returns the map.

    Args:
        segment_file: A string path to the geojson file generated by
            write_speeds_to_map_segments that should contain geometry as well
            as speed data.
        census_file: A string path to the geojson file generated by
            write_census_data_to_csv that should contain the combined s0801 and
            s1902 tables.
        colormap: A Colormap object that describes what speeds should be mapped
            to what colors.
        home_loc_value: A string of latitude and longitude for the home box
        destination_loc_value: A string of latitude and longitude of the destination
        min_income_value: A decimal value for the minimum income inputted
        max_income_value: A decimal value for the maximum income inputted

    Returns:
        A Folium Map object containing the most up-to-date speed data from the
        dynamodb.
    """
    # Read in route shapefile and give it the style function above
    kcm_routes = folium.GeoJson(
        name='King Country Metro Speed Data',
        data=f"{segment_file}_w_speeds_tmp.geojson",
        style_function=lambda feature: {
            'color': 'gray' if feature['properties']['AVG_SPEED_M_S'] == 0 \
                else colormap(feature['properties']['AVG_SPEED_M_S']),
            'weight': 1 if feature['properties']['AVG_SPEED_M_S'] == 0 \
                else 3},
        highlight_function=lambda feature: {
            'fillColor': '#ffaf00', 'color': 'blue', 'weight': 6},
        tooltip=folium.features.GeoJsonTooltip(
            fields=['ROUTE_NUM', 'AVG_SPEED_M_S',
                    'ROUTE_ID', 'LOCAL_EXPR', 'HISTORIC_SPEEDS'],
            aliases=['Route Number', 'Most Recent Speed (m/s)',
                     'Route ID', 'Local (L) or Express (E)', 'Previous Speeds']))

    # Read in the census data/shapefile and create a choropleth based on income
    seattle_tracts_df = pd.read_csv(f"{census_file}_tmp.csv")
    seattle_tracts_df['GEO_ID'] = seattle_tracts_df['GEO_ID'].astype(str)
    seattle_tracts_df['mean_income'] = pd.to_numeric(\
                                         seattle_tracts_df['mean_income'],\
                                         errors='coerce')

    # Makes the numbers smaller so the legend would look better
    seattle_tracts_df['mean_income'] = seattle_tracts_df['mean_income']/1000

    seattle_tracts_df = seattle_tracts_df.dropna()

    seattle_tracts = folium.Choropleth(
        geo_data=f"{census_file}.geojson",
        name='Socioeconomic Data',
        data=seattle_tracts_df,
        columns=['GEO_ID', 'mean_income'],
        # added thresholding values for coloring based off widget income inputs
        threshold_scale=[seattle_tracts_df["mean_income"].min()-1, \
                         int(min_income_value)/1000, \
                         int(max_income_value)/1000, \
                         seattle_tracts_df["mean_income"].max()+1],
        key_on='feature.properties.GEOID10',
        fill_color="PuBuGn",
        fill_opacity=0.7,
        line_opacity=0.4,
        legend_name='mean income (x$1000)')

    # Creates folium marker based off destination latitude and longtitude
    dest_lat = float(destination_loc_value.split(",")[0])
    dest_long = float(destination_loc_value.split(" ")[1])
    dest_marker = folium.Marker(
        location=[dest_lat, dest_long],
        popup="Destination",
        icon=folium.Icon(color="green", icon="info-sign"))

    # Creates folium marker based off home latitude and longtitude
    home_lat = float(home_loc_value.split(",")[0])
    home_long = float(home_loc_value.split(" ")[1])
    home_marker = folium.Marker(
        location=[home_lat, home_long],
        popup="Home",
        icon=folium.Icon(color="red", icon="info-sign"))

    # Draw map using the speeds and census data
    f_map = folium.Map(
        location=[47.606209, -122.332069],
        zoom_start=11,
        prefer_canvas=True)
    seattle_tracts.add_to(f_map)
    kcm_routes.add_to(f_map)
    dest_marker.add_to(f_map)
    home_marker.add_to(f_map)
    colormap.caption = 'Average Speed (m/s)'
    colormap.add_to(f_map)
    folium.LayerControl().add_to(f_map)
    return f_map

def button_execute_app(obj):
    """Sets up an executable widget to interfact with transit_vis visualization

    Run an executable widget with location coordinates and a salary range that
    utilizes the transit_vis data to create the visualization html

    Args:
        obj: widget object

    Returns:
        Widget is displayed
    """
    with OUTPUT:
        clear_output()

        if len(DESTINATION_LOC.value) > 0:
            pass
        else:
            raise ValueError("Please enter a value for your destination.")

        if len(MIN_INCOME_INPUT_BOX.value) > 0:
            pass
        else:
            raise ValueError("Please enter a value for your minimum yearly income.")


        if len(MAX_INCOME_INPUT_BOX.value) > 0:
            pass
        else:
            raise ValueError("Please enter a value for your maximum yearly income.")

        if MIN_INCOME_INPUT_BOX.value.isdecimal():
            pass
        else:
            raise ValueError("Minimum income value input must be a whole number.")

        if MAX_INCOME_INPUT_BOX.value.isdecimal():
            pass
        else:
            raise ValueError("Maximum income value input must be a whole number.")


        if int(MAX_INCOME_INPUT_BOX.value) > int(MIN_INCOME_INPUT_BOX.value):
            pass
        else:
            raise ValueError("Maximum yearly income value must be greater than minimum.")


        table_name = 'KCM_Bus_Routes'
        s0801_path = './transit_vis/data/s0801'
        s1902_path = './transit_vis/data/s1902'
        segment_path = './transit_vis/data/kcm_routes'
        census_path = './transit_vis/data/seattle_census_tracts_2010'

        print("Modifying and writing census data...")
        transit_vis.write_census_data_to_csv(s0801_path, s1902_path, census_path)

        # Connect to dynamodb
        print("Connecting to dynamodb...")
        table = transit_vis.connect_to_dynamo_table(table_name)

        # Query the dynamoDB for all speed data
        print("Getting speed data from dynamodb...")
        speed_lookup = transit_vis.table_to_lookup(table)

        print("Writing speed data to segments for visualization...")
        speeds = transit_vis.write_speeds_to_map_segments(speed_lookup, segment_path)

        plt.close("all")

        # Create the color mapping for speeds
        print("Generating map...")
        linear_cm = cm.LinearColormap(
            ['red', 'yellow', 'green'],
            vmin=0.0,
            vmax=np.ceil(np.percentile(speeds[speeds > 0.0], 95)))

        f_map = generate_folium_map_widget(segment_path,\
                                           census_path,\
                                           linear_cm,\
                                           HOME_LOC.value,\
                                           DESTINATION_LOC.value,\
                                           MIN_INCOME_INPUT_BOX.value,\
                                           MAX_INCOME_INPUT_BOX.value)

        print("Saving map...")
        transit_vis.save_and_view_map(f_map, 'output_map_widgets.html')
        return 1

# Creates home input box
HOME_LOC = widgets.Text(
    value="47.653834, -122.307858",
    placeholder='Enter Home Location in "lat, long"',
    description='Home: ',
    disabled=False,
    style={'description_width': 'initial'},
    layout=Layout(width="380px", height="auto")
)

# Creates destination input box
DESTINATION_LOC = widgets.Text(
    value="47.606209, -122.332069",
    placeholder='Enter Destination Location in "lat, long"',
    description='Destination: ',
    disabled=False,
    style={'description_width': 'initial'},
    layout=Layout(width="380px", height="auto")
)

# Creates minimum income input box
MIN_INCOME_INPUT_BOX = widgets.Text(
    placeholder='Enter minimum yearly income ($)',
    description='Income Minimum:',
    disabled=False,
    style={'description_width': 'initial'},
    layout=Layout(width="380px", height="auto")
)

# Creates maximum income input box
MAX_INCOME_INPUT_BOX = widgets.Text(
    placeholder='Enter maximum yearly income ($)',
    description='Income Maximum:',
    disabled=False,
    style={'description_width': 'initial'},
    layout=Layout(width="380px", height="auto")
)

# Creates a clickable button to execute a function based off inputs
APP_BUTTON = widgets.Button(description='Generate Map',\
                            layout=Layout(width="380px", height="auto"))

# A function which executes upon app_button being clicked and executes verifications
## as well as filter and output the map
APP_BUTTON.on_click(button_execute_app)

# Combines all input boxes and widget together
INPUT_BOX = VBox([HOME_LOC, DESTINATION_LOC, MIN_INCOME_INPUT_BOX,\
                  MAX_INCOME_INPUT_BOX, APP_BUTTON])

# Assigns an output widget to display the output from the executed function
# and allow for overwriting
OUTPUT = widgets.Output()

display(INPUT_BOX)
display(OUTPUT)
