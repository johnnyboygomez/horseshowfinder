# horseshowfinder
### Saddle Up! Canadian Horse Shows Heat Map By Discipline

**Video Demo:** [https://youtu.be/gtxQ-K2zP90](https://youtu.be/gtxQ-K2zP90) 

**Web App URL:** https://www.stableright.io/horseshowfinder

**Student:** John Dowling  
**edX:** JD_2407_MPGF  
**GitHub:** [johnnyboygomez/horseshowfinder](https://github.com/johnnyboygomez/horseshowfinder)

![Canadian Horse Show Heat Map](https://stableright.io/horseshowfinder/horseshowfinder.png)

This interactive map displays horse shows across Canada, categorized by discipline: **Jumping**, **Eventing**, and **Dressage** (the three Olympic disciplines). Users can filter the map to display only a specific discipline and click on individual markers to view show details.

Show data is scraped from the Equine Canada website, cached locally, and updated hourly.

Built using **HTML**, **JavaScript**, **Leaflet.js**, and **Leaflet.markercluster**, the app reads data from `heatmap.json` and organizes it visually for clarity and usability.

**What is the point?**<br>
This app attempts to fill a gap in the usefullness of an existing public API by making it very easy to find information quickly via an interactive map of the country. 


---

### Features

- Interactive Leaflet map with marker clustering
- Show markers color-coded by discipline
- Discipline filter buttons (Jumping / Eventing / Dressage)
- Marker popups with show name, dates, veniue, location, and web link
- Responsive layout for desktop and mobile


#### How to Use

1. Open [stableright.io/horseshowfinder/index.html](http://stableright.io/horseshowfinder/index.html) in your browser.
2. Use the **dropdown menu** at the top to filter shows by discipline (Jumping, Eventing, or Dressage).
3. **Click on a marker** or **cluster** to zoom in and explore specific events.
4. If a cluster doesn’t respond on the first click, try clicking again — this is a known flicker issue.
5. Click any **individual marker** to view detailed information:
   - Event name, date, and location
   - Link to the Equine Canada page (if results are available)
   - Link to the event’s own website (if extant)

## Application Walkthrough (How It Works) 

#### File Structure

```plaintext
/project-folder
│
├── heat.py              # Python script that creates the following JSON files 
├── heatmap.json         # Data file with show listings
├── geocode_cache.json   # Corrected latitude and longitude of each venue
├── index.html           # Main HTML file with map and logic
├── styles.css           # CSS styling for filter and layout

```

**Dependencies**<br>
- [Leaflet.js](https://leafletjs.com/) — Interactive maps
- [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) — Marker clustering plugin

These libraries are loaded via **CDN** in `index.html`.

The key file is `heat.py`. This is a python script that is run from the command line. I decided to extract all the information for the map at once and to save it in a json file rather than fetching the info on the fly. This made the map very fast. In order to be sure the info is up to date I created a cron job to run the script hourly. This is more than adequate for the users' needs. 
```
0 * * * * /usr/bin/python3 /home/dh_4c4v8n/stableright.io/horseshow/heat.py >> /home/dh_4c4v8n/stableright.io/horseshow/heat.log 2>&1
````
### Psuedocode

1. Fetch data on all recognized horse shows using `get_all_shows()`
2. Get location details and show IDs with `extract_location_details()`
3. For each horse show, use `geocode_locations()` to:
   1. First check `geocode_cache.json`:
      - If location exists, reuse existing coordinates (longitude, latitude)
      - If not, geocode it (find loordinates using Nominatim from OpenStreetMap) and add to the cache
   3. Fetch additional show info via API with `get_show_info()`
   4. Append show and location details to `heatmap.json`
<br>

**API Notes**<br>
The data is drawn from the API of Equine Canada. For example, this url will call a json file with all recognized horse shows in 2025:
`https://events.equestrian.ca/CreateTokenWCF.svc/GetShowsList?province=&discipline=&year=2025&type=&results=`

This is a sample object:
```{
Cancelled: false,
ContactEmail: null,
ContactName: null,
ContactPhone: null,
Discipline: "jumping",
EndDate: "/Date(1738472400000-0500)/",
Id: 250164,
Level: "Bronze",
Location: "SPRUCE MEADOWS, CALGARY, AB",
Money: 0,
Name: "2025 SPRUCE MEADOWS FEBRUARY CLASSIC I",
PendingResults: false,
Province: "AB",
Results: false,
StartDate: "/Date(1738299600000-0500)/",
Website: null
}
```
Furthermore, once you have the show ID you can do a second search based on the show ID. For example: `https://events.equestrian.ca/CreateTokenWCF.svc/GetShowInfo?id=250164`

```
{
Cancelled: false,
ContactEmail: "joanne.nimitz@sprucemeadows.com",
ContactName: "Joanne Nimitz",
ContactPhone: "4039744250",
Discipline: "HJ",
EndDate: "/Date(1738472400000-0500)/",
Id: 250164,
Level: "Bronze",
Location: "SPRUCE MEADOWS, CALGARY, AB",
Money: 0,
Name: "2025 SPRUCE MEADOWS FEBRUARY CLASSIC I",
PendingResults: false,
Province: null,
Results: false,
StartDate: "/Date(1738299600000-0500)/",
Website: "www.sprucemeadows.com"
}
```
Note that some items listed as null in the first search (such as contact info) are actually list in the detailed show info.

#### Cleaning Data ####
There were two serious problems with the geolocation data: inconsistent nonclemature of placenames and venues, and incorrect locations of the venues. 
1. Errors occurred in the json file from the API. City names were missplelled, venue and city names were transposed, extra commas showed up, etc. Since I have no control over the API I decided to create a list of all corrections cse by case. I created a dictionary, `corrected_locations`, that could be used to correct erroneous place names and thus be presented properly on the map. HEre is a snippet:
```
"RED RIVER EXHIBITION PARK, WINNIPEG, MB , MB": "RED RIVER EXHIBITION PARK, Winnipeg, MB",
    "LAKESIDE, FOSHAY SOUTH EVENTING, NB": "FOSHAY SOUTH EVENTING, Lakeside, NB",
    "RAINBOW RIDERS, ST.JOHNS, NL": "Rainbow Riders, St. John's, NL",
    "EQUESTRAN FARM, VAUDREIL, QC": "EQUESTRAN FARM, Vaudreuil, QC",
    "WESLEY CLOVER PARKS , ON": "WESLEY CLOVER PARKS, Ottawa, ON",
```
2. Because we only have the city and province without street locations, Nominatim provides the downtown crossroads as the coordinates. For example Wesley Clover Parks is shown in downtown Ottawa. It is actually 26 km west of there! My solution was to get each venue's coordinates on google maps and then update `geocode_cache.json` by hand. This only needs to be done once per venuse, even it the venue has many shows. So what's the point in using a geocoded service if it all has to be changed? It actually is helpful for a few reasons. First it allows the program to run and be debugged and tweaked knowing that the locations are  close to accurate coompared to the size ot the country. Also, geocode_cache.json is a nice neat file to open and simply change long and lat, and nothing else.

## Frontend ##

Users access the app via **index.html**.

The **<head>** imports the **stylesheets**:
- [Leaflet](https://unpkg.com/leaflet/dist/leaflet.css)
- [MarkerCluster Default](https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.Default.css)
- [MarkerCluster Layout](https://unpkg.com/leaflet.markercluster/dist/MarkerCluster.css)
- [styles.css](https://stableright.io/horseshowfinder/styles.css)

and these **scripts**:
- [Leaflet](https://unpkg.com/leaflet/dist/leaflet.js) — An open-source JavaScript library for mobile-friendly interactive maps  
- [MarkerCluster](https://unpkg.com/leaflet.markercluster/dist/leaflet.markercluster.js) — Enhances Leaflet by clustering dense datasets into a clean, usable view  
- [https://stableright.io/horseshowfinder/horseshowfinder.js](https://stableright.io/horseshowfinder/horseshowfinder.js) — Custom logic for marker rendering, filtering, and popup handling

#### horseshowfinder.js ####
1. Defines custom Leaflet marker icons (blue, green, violet, grey) for Jumping, Eventing, Dressage, and a fallback "other" category.

These icons use a github user content image URL for marker visuals and include standard Leaflet shadow images, [https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png](https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png)

2. Responsive Map Configuration
Checks the screen width to detect mobile devices (<= 500px).

Initializes the map with an integer zoom level (3 for mobile, 4 for desktop).

Then immediately sets a more precise zoom level using map.setZoom() (e.g., 3.5 or 4.6) to allow fractional zoom since Leaflet doesn’t support it directly in the initial call.

```
const isMobile = window.innerWidth <= 768;

const map = L.map("map", {
  center: [50.0, -90.0],
  zoom: isMobile ? 3 : 4, // must be integer here
  zoomSnap: 0.1,
  maxZoom: 11,
});

// Apply fractional zoom after initialization
if (isMobile) {
  map.setZoom(3.5);
} else {
  map.setZoom(4.6); // Or whatever default you prefer for desktop
}

```

3. Tile Layer
Adds OpenStreetMap tiles to the map as the visual base layer.
```
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);
```

4. Fetch JSON Data
Loads heatmap.json, which contains an array of show/event objects with properties like latitude, longitude, name, discipline, dates, and result status.

5. MarkerCluster Setup
Initializes a MarkerClusterGroup to automatically group close-together markers and adds a clusterclick handler so when a cluster is clicked, the map zooms to fit its bounds smoothly.
```
fetch("heatmap.json")
    .then((response) => response.json())
    .then((data) => {
      const markerGroup = L.markerClusterGroup({
        zoomToBoundsOnClick: false,
      });

      markerGroup.on("clusterclick", (a) => {
        map.fitBounds(a.layer.getBounds(), {
          padding: [0, 70],
          maxZoom: 13,
          animate: true,
        });
      });
```

6. Marker Creation
- For each event in the dataset:

- Determines the correct icon based on the discipline.

- Creates a marker at the latitude/longitude coordinates.

- Builds a popup HTML string using event data:

- Show name and venue.

- Dates (with special handling for cancelled events).

- Discipline and competition level.

- Result status and link (if available).

- Competition website (if available, prepends `https://` if needed).

- Attaches the popup and discipline to the marker.

- Adds the marker to the cluster group and stores it in an `allMarkers` array.

- Once all markers are created and added to the cluster group, the entire group is added to the map.

7. Checkbox UI Filtering
- Selects all .discipline-checkbox inputs.

- Adds an event listener to each checkbox.

- When checkboxes are changed:

- The script filters the allMarkers array to include only those matching the selected disciplines.

- Clears the cluster group and re-adds only the filtered markers.

```
const checkboxes = document.querySelectorAll(".discipline-checkbox");

```
8. Fix Map Layout
After a short delay (100ms), it calls map.invalidateSize() to fix any rendering issues that can occur after programmatically adjusting zoom or adding many markers.


