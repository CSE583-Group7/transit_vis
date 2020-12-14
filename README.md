[![Build Status](https://travis-ci.org/CSE583-Group7/transit_vis.svg?branch=main)](https://travis-ci.org/CSE583-Group7/transit_vis)
[![Coverage Status](https://coveralls.io/repos/github/CSE583-Group7/transit_vis/badge.svg?branch=main&service=github)](https://coveralls.io/github/CSE583-Group7/transit_vis?branch=main&service=github)
## Where's My Bus?
Team: Zack Aemmer, Kelly Balmes, Alex Goldstein, Steven Wilson | CSE 583 Software Development for Data Scientists

### Background
Transit delays are unavoidable, and transit agencies often plan for them through practices such as schedule padding. While this can improve the reliability of transit systems by allowing for delays to occur and stay on schedule, it does not improve their efficiency. The General Transit Feed Specification Realtime (GTFS-RT) has provided a generalized set of real-time transit data to be released to the public, allowing for the precise location of transit delays. This provides a neatly packaged programming interface for Automatic Vehicle Location (AVL) data that is otherwise proprietary and confined to individual bus systems. From an urban planning perspective, it is useful to understand who is impacted most by transit delays, and to determine where these delays occur so that the impacts to various communities can be mitigated, if possible. At its core, this project develops a visualization tool that is capable of displaying locations of bus delay from the King County Metro GTFS-RT feed, and overlaying them with socioeconomic data from the American Community Survey (ACS) so that planners and community members in Seattle can visually determine areas where transit is slow and who is affected. It has the added benefit of being constructed on the GTFS-RT standard, so that it is easily extendable to any other transit agency which repackages its individual AVL data in the GTFS-RT format.

### Sample Map
![Screenshot of Sample Map with Speed and Socioeconomic Data](example_output.png?raw=true "Example")

### Transit Vis Setup
Prior to installing this project, make sure to install [anaconda](https://anaconda.org/)

Once anaconda is installed:
1. clone the repository: git clone https://github.com/CSE583-Group7/transit_vis.git 
2. create the necessary conda environment: conda env create -q -n transit_vis --file environment.yml
3. activate the conda environment: conda activate transit_vis
If setting up the backend for a new transit vis network:
4. Create AWS-RDS database using create_gtfs_tables.sql; scrape GTFS-RT source data to this location
5. Copy AWS credentials for the account that data has been saved to in config.py
6. From terminal run once: python3 initialize_dynamodb.py
7. From terminal run daily: python3 summarize_rds.py
If using an existing transit vis backend:
4. Copy AWS credentials for the account that data has been saved to in config.py

### Transit Vis Operation
Once setup has been completed, the map can be generated and viewed for analysis:
1. From terminal run: python3 generate_transit_vis_map.py
2. Copy and paste output_map.html (including local file path) into any browser to display output data, or open the output_map.html file located in the /src directory 

### Project Directory Organization
The project is within the "transit_vis" directory. The project is further organized into three main directories:
* src (main scripts to execute)
* tests (scripts to test the functions are properly working)
* data (geojson and csv files of transit and socioeconmic data)

### Generated Files
During tool operation, several files are created in the data/ folder:
* kcm_routes_w_speeds_tmp.geojson: A shapefile with added properties containing the speed data from the most recent run of the tool
* seattle_census_tracts_2010_tmp.csv: A data file containing the combined s0801 and s1902 census tables
* google_transit.zip/google_transit: A zip file and extracted folder containing the most up to date GTFS (tripids, routeids, stopids, etc.) information from King County Metro
After running the tool, one file is created in the src/ folder:
* output_map.html: The final result from the most recent run which can be viewed in any web browser.

```
transit_vis/
  |- README.md
  |- LICENSE.md
  |- transit_vis/  
     |- src/
        |- generate_transit_vis_map.py
        |- initialize_dynamodb.py
        |- summarize_rds.py
        |- transit_vis.py
        |- vis_functions.py
        |- create_gtfs_tables.sql
     |- tests/
        |- test_transit_vis.py
     |- data/
        |- kcm_routes.geojson
        |- s0801.csv
        |- s1902.csv
        |- seattle_census_tracts.geojson
  |- docs/
     |- component_specification.md
     |- functional_specification.md 
```

### Project Data
GTFS-RT Transit Data:
* [King County Metro GTFS-RT Data](http://developer.onebusaway.org/modules/onebusaway-application-modules/current/api/where/index.html)

GTFS Transit Data:
* [King County Metro GTFS Data](http://metro.kingcounty.gov/gtfs/)

Socioeconomic Data:
* [American Community Survey (ACS)](https://www.census.gov/programs-surveys/acs/data.html)

Shapefiles:
* [King Country Metro All Routes](https://www5.kingcounty.gov/sdc/TOC.aspx?agency=transit)
* [TIGER Census Tracts](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)
