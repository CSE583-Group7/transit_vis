[![Build Status](https://travis-ci.org/CSE583-Group7/transit_vis.svg?branch=main)](https://travis-ci.org/CSE583-Group7/transit_vis)
[![Coverage Status](https://coveralls.io/repos/github/CSE583-Group7/transit_vis/badge.svg?branch=main&service=github)](https://coveralls.io/github/CSE583-Group7/transit_vis?branch=main&service=github)
## Where's My Bus?
Team: Zack Aemmer, Kelly Balmes, Alex Goldstein, Steven Wilson | CSE 583 Software Development for Data Scientists

### Background
Transit delays are unavoidable, and transit agencies often plan for them through practices such as schedule padding. While this can improve the reliability of transit systems by allowing for delays to occur and stay on schedule, it does not improve their efficiency. The General Transit Feed Specification Realtime (GTFS-RT) has provided a generalized set of real-time transit data to be released to the public, allowing for the precise location of transit delays. This provides a neatly packaged programming interface for Automatic Vehicle Location (AVL) data that is otherwise proprietary and confined to individual bus systems. From an urban planning perspective, it is useful to understand who is impacted most by transit delays, and to determine where these delays occur so that the impacts to various communities can be mitigated, if possible. At its core, this project develops a visualization tool that is capable of displaying locations of bus delay from the King County Metro GTFS-RT feed, and overlaying them with socioeconomic data from the American Community Survey (ACS) so that planners and community members in Seattle can visually determine areas where transit is slow and who is affected. It has the added benefit of being constructed on the GTFS-RT standard, so that it is easily extendable to any other transit agency which repackages its individual AVL data in the GTFS-RT format.

### Sample Map
![Screenshot of Sample Map with Speed and Socioeconomic Data](example_output.png?raw=true "Example of Tool Output")

### Transit Vis Setup
Prior to installing this project, make sure to install [anaconda](https://anaconda.org/)

#### Once anaconda is installed:
1. From terminal clone the repository: git clone https://github.com/CSE583-Group7/transit_vis.git
2. From terminal create the conda environment: conda env create -q -n transit_vis --file environment.yml
3. From terminal activate the conda environment: conda activate transit_vis

#### If setting up the backend for a new transit vis network:
4. Create RDS database using create_gtfs_tables.sql. Scrape GTFS-RT source data to this location  
5. Copy AWS credentials for the account holding the transit data to config.py
6. From terminal run once: python -m transit_vis.src.initialize_dynamodb
7. From terminal run daily: python -m transit_vis.src.summarize_rds

#### If using an existing transit vis backend:
4. Copy AWS credentials for the account holding the transit data to config.py

### Transit Vis Operation
Once setup has been completed, the map can be generated and viewed for analysis:
1. From terminal run: python -m transit_vis.src.transit_vis
2. Copy and paste output_map.html (including local file path) into any browser to display output data, or open the output_map.html file located in the /src directory 

### Project Directory Organization
The project is within the "transit_vis" directory. The project is further organized into three main directories:
* src (main scripts to execute)
* tests (scripts to test the functions are properly working)
* data (geojson and csv files of transit and socioeconmic data)

Copies of all files in the "data" directory including files generated during operation are kept in the tests directory for the purpose of keeping test results separate from actual results when running the unit tests.

#### Included Files
```
transit_vis/
  |- README.md
  |- LICENSE.md
  |- transit_vis/  
     |- src/
        |- initialize_dynamodb.py
        |- summarize_rds.py
        |- transit_vis.py
        |- create_gtfs_tables.sql
     |- tests/
        |- test_transit_vis.py
        |- data/
           |- kcm_routes.geojson
           |- ...
     |- data/
        |- kcm_routes.geojson
        |- s0801.csv
        |- s1902.csv
        |- seattle_census_tracts.geojson
  |- docs/
     |- component_specification.md
     |- functional_specification.md 
```
#### Generated Files
Created in the data folder during tool operation:
* **kcm_routes_w_speeds_tmp.geojson:** A shapefile with added properties containing the speed data from the most recent run of the tool
* **seattle_census_tracts_2010_tmp.csv:** A data file containing the combined s0801 and s1902 census tables
* **google_transit.zip/google_transit:** A zip file and extracted folder containing the most up to date GTFS (tripids, routeids, stopids, etc.) information from King County Metro
* **kcm_routes_histogram.png:** An image file that shows the distribution of transit speeds for the entire network from the most recent run.

Created in the top-level folder during tool operation:
* **output_map.html:** The final result from the most recent run which can be viewed in any web browser.

### Project Data Sources
Transit Location/ID Data:
* [King County Metro GTFS-RT Data](http://developer.onebusaway.org/modules/onebusaway-application-modules/current/api/where/index.html)
* [King County Metro GTFS Data](http://metro.kingcounty.gov/gtfs/)

Socioeconomic Data:
* [American Community Survey (ACS)](https://www.census.gov/programs-surveys/acs/data.html)

Shapefile Data:
* [All King Country Metro Routes](https://www5.kingcounty.gov/sdc/TOC.aspx?agency=transit)
* [TIGER Census Tracts](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)