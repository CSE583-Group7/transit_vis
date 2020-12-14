[![Build Status](https://travis-ci.org/CSE583-Group7/transit_vis.svg?branch=main)](https://travis-ci.org/CSE583-Group7/transit_vis)
[![Coverage Status](https://coveralls.io/repos/github/CSE583-Group7/transit_vis/badge.svg?branch=main&service=github)](https://coveralls.io/github/CSE583-Group7/transit_vis?branch=main&service=github)
## Where's My Bus?
Team: Zack Aemmer, Kelly Balmes, Alex Goldstein, Steven Wilson | CSE 583 Software Development for Data Scientists

### Background:
Transit delays are unavoidable, and transit agencies often plan for them through practices such as schedule padding. While this can improve the reliability of transit systems by allowing for delays to occur and stay on schedule, it does not improve their efficiency. The General Transit Feed Specification Realtime (GTFS-RT) has provided a generalized set of real-time transit data to be released to the public, allowing for the precise location of transit delays. This provides a neatly packaged programming interface for Automatic Vehicle Location (AVL) data that is otherwise proprietary and confined to individual bus systems. From an urban planning perspective, it is useful to understand who is impacted most by transit delays, and to determine where these delays occur so that the impacts to various communities can be mitigated, if possible. At its core, this project develops a visualization tool that is capable of displaying locations of bus delay from the King County Metro GTFS-RT feed, and overlaying them with socioeconomic data from the American Community Survey (ACS) so that planners and community members in Seattle can visually determine areas where transit is slow and who is affected. It has the added benefit of being constructed on the GTFS-RT standard, so that it is easily extendable to any other transit agency which repackages its individual AVL data in the GTFS-RT format.

![Screenshot of Sample Map with Speed and Socioeconomic Data](example_output.png?raw=true "Example")

### Installation and Operation
Prior to installing this project, make sure to install [anaconda](https://anaconda.org/)

Once anaconda is installed:
1. clone the repository: git clone https://github.com/CSE583-Group7/transit_vis.git 
2. create the necessary conda environment: conda env create -q -n transit_vis --file environment.yml
3. activate the conda environment: conda activate transit_vis
4. obtain a copy of config.py
5. run: python3 initialize_dynamodb.py
6. run daily: python3 summarize_rds.py

Once steps 1-6 have been completed, the map can be generated and viewed for analysis:
1. run from the terminal: python3 generate_transit_vis_map.py
2. copy and paste output_map.html (including local file path) into any browser to display output data

### Project Directory Organization
The project is within the "transit_vis" directory. The project is further organized into three main directories:
* src (main scripts to execute)
* tests (scripts to test the functions are properly working)
* data (geojson and csv files of transit and socioeconmic data)

```
transit_vis/
  |- readme.md
  |- license.md
  |- transit_vis/  
     |- src/
        |- generate_transit_vis_map.py
        |- initialize_dynamodb.py
        |- summarize_rds.py
        |- transit_vis.py
        |- vis_functions.py
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
* Transit Data
- King County Metro Data

* Socioeconomic Data
- American Community Survey (ACS)