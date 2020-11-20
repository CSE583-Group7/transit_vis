# Transit Visualization Tool Functional Specification

## Background
Transit delays are unavoidable, and transit agencies often plan for them through practices such as schedule padding. While this can improve the reliability of transit systems by allowing for delays to occur and stay on schedule, it does not improve their efficiency. The General Transit Feed Specification Realtime (GTFS-RT) has provided a generalized set of real-time transit data to be released to the public, allowing for the precise location of transit delays. This provides a neatly packaged programming interface for Automatic Vehicle Location (AVL) data that is otherwise proprietary and confined to individual bus systems. From an urban planning perspective, it is useful to understand who is impacted most by transit delays, and to determine where these delays occur so that the impacts to various communities can be mitigated, if possible. At its core, this project develops a visualization tool that is capable of displaying locations of bus delay from the King County Metro GTFS-RT feed, and overlaying them with socioeconomic data from the American Community Survey (ACS) so that planners in Seattle can visually determine areas where transit is slow and who is affected. It has the added benefit of being constructed on the GTFS-RT standard, so that it is easily extendable to any other transit agency which repackages its individual AVL data in the GTFS-RT format. 

## User Profile
Our target users fall into two main groups: professionals who would like to draw high-level insights on transit delays in Seattle, and community members who want information on transit delays in particular neighborhoods.

**Professionals:**<br>
This group of users has background knowledge on transit operations in the Seattle area, but are not necessarily programmers or computer scientists. These users are interested in understanding where transit delays occur, and who they impact. Our tool should provide them with the means to explore our datasets, and perform their own analytical work on the underlying data.

**Community Members:**<br>
This group of users has minimal background knowledge on transit operations or programming. They are not interested in re-using the data outside of our tool, or drawing insights outside of the visualization itself. These users are looking for a quick, easy tool interface that will tell them what they need to know about transit delays in a neighborhood of interest.

## Data Sources
**Bus Delays:**<br>
The foundation of our tool is a dataset scraped daily from the OneBusAway API. This data contains variables for bus identifiers, locations, delays, times, and distances along trips. This data is scraped at a 10 second rate between the hours of 6AM and 8PM. In order to determine transit speeds, we take individual tracked locations and determine the distance between them, and the time it took to traverse that distance. This data is then aggregated to routes and segments. This data is scraped by an AWS EC2 instance and stored in AWS RDS running PostgreSQL. The dataset itself is quite large, and our tool necessitates quick querying and interaction. For that reason, each day's data is queried at the end of the day and summarized in a dynamoDB instance, which then directly interfaces with our application.

**Socioeconomic Census Data:**<br>
Our tool overlays socioeconomic data at the census tract level across King County. This data is drawn from the American Community Survey (ACS) data tables for basic economic and demographic statistics. ACS data is aggregated by various geographies, and in the future a lower resolution (block groups or smaller) could be used to see a finer grained visualization. ACS data is drawn from the 2017, 5-year census survey, which is the most up-to-date version available. This version still contains the complete set of data tables at the census tract level.

**Shapefiles:**<br>
To facilitate the visualization of our data, we use Python libraries to plot shapefiles stored in GeoJSON format. We use 2 shapefiles each containing many features. The first contains the complete set of bus routes operated by King County Metro. Not all of these routes are current, so a grey, transparent color scheme is applied to routes in the visualization that do not have data. The second shapefile contains census tract shapes for all tracts in King County. These shapes are overlaid on the map and given a color scheme according to their underlying socioeconomic data. Beneath both shapefiles, our visualization uses the OpenStreetMap basemap tiles.

## Use Cases
1) Professional user wishes to view transit speeds throughout a particular corridor on the map, and compare them to historic levels.
* In this case, the user's objective is to get data for a specific location on our map, and download that data for their own analysis.
* The user will achieve this by viewing our map, zooming in to the location of interest, and selecting segments/stops within their analysis corridor. We will allow them to do this through filtering widgets, and mouse based selection on the visualization map. One such filter will be a timeline across which to display average speeds for a segment. Once a subset of our data is selected through the map interface, the user will be able to click a button to download the underlying data in CSV format. This will alow the user to combine our data with their data for further analysis.

2) Community Member wishes to view typical transit speeds in different neighborhoods, for the sake of choosing a place to live within a specific commute time.
* In this case, the user's objective is to estimate a transit accessibility radius from a particular point on the map. This will allow them to choose a work location and maximum allowable commute time, and determine a range of neighborhoods that are accessible by transit.
* The user will achieve this by selecting a location on the map, and clicking a button to display the accessibility radius. Our tool will do all of the work on the backend, by gathering transit speeds for nearby segments, and creating an estimate for how far someone might be able to travel by transit in the specified time. The output will be an accessibility radius, which will be displayed on the map.
