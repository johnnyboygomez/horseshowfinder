import requests
import json
import time
from datetime import datetime
from geopy.geocoders import Nominatim
import logging
import re

# Configure logging
logging.basicConfig(
    filename="horse_show_log.txt",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Initialize geocoder
geolocator = Nominatim(user_agent="horse-show-map")

# Corrections for bad city/province values
location_corrections = {
    "RED RIVER EXHIBITION PARK, WINNIPEG, MB , MB": "RED RIVER EXHIBITION PARK, Winnipeg, MB",
    "RED RIVER EXHIBITION PARK, WINNIPEG, MB, MB": "RED RIVER EXHIBITION PARK, Winnipeg, MB",
    "LAKESIDE, FOSHAY SOUTH EVENTING, NB": "FOSHAY SOUTH EVENTING, Lakeside, NB",
    "MERRITT, BC": "Merritt, BC",
    "RAINBOW RIDERS, ST.JOHNS, NL": "Rainbow Riders, St. John's, NL",
    "EQUESTRAN FARM, VAUDREIL, QC": "EQUESTRAN FARM, Vaudreuil, QC",
    "WESLEY CLOVER PARKS , ON": "WESLEY CLOVER PARKS, Ottawa, ON",
    "COMPLEXE EQUESTRE BECANCOUR, QC": "COMPLEXE EQUESTRE BECANCOUR, Becancour, QC",
    "LES ECURIES DE LA CHAUDIERE, QC": "LES ECURIES DE LA CHAUDIERE, Lévis, QC",
    "CENTRE-EQUESTRE MONT ROUGE, QC": "CENTRE-EQUESTRE MONT ROUGE, Saint-Jean-Baptiste, QC",
    "SUTTON, QUEBEC, QC": "Sutton, QC",
    "LES ECURIES KADELLO , QC": "LES ECURIES KADELLO, Mascouche, QC",
    "PARC EQUESTRE DE BROMONT, QC": "PARC EQUESTRE DE BROMONT, Bromont, QC",
    "PICKERING HORSE CENTRE, PICKERING, ON , ON": "PICKERING HORSE CENTRE, Pickering, ON",
    "BONNIE BRAE FARM, BC": "BONNIE BRAE FARM, Saanichton, BC",
    "560 Snyder's Rd E Baden, ON": "560 Snyder's Rd E, Baden, ON",
    "ROCKY MOUNTAIN SHOW JUMPING, CALGARY,, AB": "ROCKY MOUNTAIN SHOW JUMPING, Dewinton, AB",
    "ROCKY MOUNTAIN SHOW JUMPING, CALGARY, AB": "ROCKY MOUNTAIN SHOW JUMPING, Dewinton, AB",
    "CALEDON EQUESTRIAN PARK, CALEDON, ON": "CALEDON EQUESTRIAN PARK, PALGRAVE, ON",
    "CALEDON EQUESTRIAN PARK, CALEDON, ON , ON": "CALEDON EQUESTRIAN PARK, PALGRAVE, ON",
    "CALEDON, ON": "CALEDON RIDING CLUB, CALEDON, ON",
    "MOOSE JAW EXHIBITION, SK": "MOOSE JAW EXHIBITION, Moose Jaw, SK",
    "ANCASTER FAIRGROUNDS, ON": "ANCASTER FAIRGROUNDS, Ancaster, ON",
    "BOBCAYGEON, ON": "Lane's End Farm, Bobcaygeon, ON",
    "RANG DES PATRIOTES NAPIERVILLE, QC": "Écurie la Crinière, Napierville, QC",
    "Campbell Valley Regional Park, Langley, BC": "Campbell Valley Regional Park, Langley Twp, BC",
    "ANGELSTONE TOURNAMENTS, ERIN, ON": "ANGELSTONE TOURNAMENTS, ROCKWOOD, ON",
    "ANGELSTONE TOURNAMENTS, ROCKWOOD, ON , ON": "ANGELSTONE TOURNAMENTS, ROCKWOOD, ON",
    "QUANTUM FARM, KARS, ON": "QUANTUM FARM, 6630 Third Line Rd Kars, ON",
    "SUTTON, QUEBEC, QC": "Les Écuries Avalon, Sutton, QC",

}

# Load geocode cache if it exists
try:
    with open("geocode_cache.json", "r") as f:
        geocode_cache = json.load(f)
except FileNotFoundError:
    geocode_cache = {}

def get_all_shows(year):
    url = f"https://events.equestrian.ca/CreateTokenWCF.svc/GetShowsList?&province=&Discipline=&year={year}&type=&results="
    logging.info(f"Requesting all shows for year {year}")
    print(f"Requesting all shows for year {year}")
    response = requests.get(url, timeout=10)
    data = response.json()
    return data.get("data", [])

def extract_location_details(shows):
    locations = []
    allowed_disciplines = {"eventing", "jumping", "dressage"}
    print("Extracting Location Details")
    for show in shows:
        discipline = str(show.get("Discipline", "")).strip().lower()
        if discipline not in allowed_disciplines:
            logging.info(f"Skipping show with discipline '{discipline}'")
            continue

        raw_loc = str(show.get("Location", "")).strip()
        # Normalize all whitespace (spaces, tabs, newlines) to single space
        normalized_loc = re.sub(r'\s+', ' ', raw_loc).strip()
        # Convert to uppercase for matching corrections
        lookup_key = normalized_loc.upper()
        # Apply correction if available, otherwise use normalized location
        corrected_loc = location_corrections.get(lookup_key, normalized_loc)
        show_id = show.get("Id", "")
        name = show.get("Name", "Unknown")

        if not corrected_loc:
            logging.warning(f"Skipping show with missing location: {name} (ID: {show_id})")
            continue

        parts = [p.strip() for p in corrected_loc.split(",")]
        if len(parts) >= 3:
            venue = parts[0].title()
            city = parts[-2].title()
            province = parts[-1].upper()
        elif len(parts) == 2:
            venue = parts[0].title()
            city = parts[0].title()
            province = parts[1].upper()
        else:
            logging.warning(f"Skipping malformed location: {corrected_loc} for show {name} (ID: {show_id})")
            continue

        locations.append({
            "venue": venue,
            "city": city,
            "province": province,
            "discipline": discipline,
            "show_id": show_id
        })
    return locations


def geocode_locations(event_data, geolocator, geocode_cache, location_corrections):
    geocoded = []
    print("Geocoding locations")
    for event in event_data:
        loc_key = f"{event['city']}, {event['province']}"
        venue = event.get("venue", "")

        # Apply corrections
        if loc_key in location_corrections:
            corrected = location_corrections[loc_key]
            logging.info(f"Corrected location from '{loc_key}' to '{corrected}'")
            print(f"Corrected location from '{loc_key}' to '{corrected}'")
            loc_key = corrected

        # Retrieve from cache or geocode
        if loc_key in geocode_cache:
            geo = geocode_cache[loc_key]
        else:
            try:
                ##logging.info(f"Geocoding: {loc_key}")
                result = geolocator.geocode(loc_key)
                time.sleep(1)
                if result:
                    geo = {
                        "lat": result.latitude,
                        "lng": result.longitude
                    }
                    geocode_cache[loc_key] = geo
                else:
                    logging.error(f"Could not geocode: {loc_key}")
                    continue
            except Exception as e:
                logging.exception(f"Error geocoding {loc_key}")
                continue

        # Save enriched event
        enriched = {
            "city_province": loc_key,
            "venue": venue,
            "lat": geo["lat"],
            "lng": geo["lng"],
            "discipline": event.get("discipline", ""),
            "level": event.get("level", ""),
        }
        show_id = event.get("show_id")
        show_info = get_show_info(show_id)
        enriched.update(show_info)
        geocoded.append(enriched)

    return geocoded

def get_show_info(show_id):
    ## logging.info(f"Called get_show_info with ID: {show_id}")
    try:
        url = f"https://events.equestrian.ca/CreateTokenWCF.svc/GetShowInfo?id={show_id}"
        ## logging.info(f"Fetching show info for ID: {show_id}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        raw_start = data.get("StartDate", "")
        raw_end = data.get("EndDate", "")
        logging.debug(f"Raw StartDate for ID {show_id}: {raw_start}")
        logging.debug(f"Raw EndDate for ID {show_id}: {raw_end}")

        def parse_dotnet_date(dotnet_str):
            if not dotnet_str:
                return "Unknown"
            try:
                timestamp = int(dotnet_str.strip("/Date()").split("-")[0])
                return datetime.utcfromtimestamp(timestamp / 1000).strftime('%B %-d, %Y')
            except Exception as e:
                logging.error(f"Error parsing date string '{dotnet_str}': {e}")
                return "Unknown"
        
        return {
            "start_date": parse_dotnet_date(raw_start),
            "end_date": parse_dotnet_date(raw_end),
            "cancelled": str(data.get("Cancelled")),
            "results": str(data.get("Results")),
            "name": str(data.get("Name")),
            "pending_results": str(data.get("PendingResults")),
            "website": str(data.get("Website")),
            "level": str(data.get("Level")),
            "show_id": (show_id)
        }
    except Exception as e:
        logging.exception(f"Error fetching show info for {show_id}")
        return {
            "start_date": "Unknown",
            "end_date": "Unknown"
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate a heatmap of equestrian competition venues.")
    parser.add_argument("--year", type=int, default=2025, help="Year to process (default: 2025)")
    args = parser.parse_args()

    year = args.year

    logging.info(f"Starting horse show map enrichment process for year {year}...")
    print(f"Starting horse show map enrichment process for year {year}...")
    shows = get_all_shows(year)
    locations = extract_location_details(shows)
    geocoded = geocode_locations(locations, geolocator, geocode_cache, location_corrections)

    with open("heatmap.json", "w") as f:
        json.dump(geocoded, f, indent=2, ensure_ascii=False)
        print(f"Opening heatmap.json")
    with open("geocode_cache.json", "w") as f:
        json.dump(geocode_cache, f, indent=2)

    logging.info(f"Geocoded and enriched {len(geocoded)} locations.")
    print(f"Geocoded and enriched {len(geocoded)} locations.")
