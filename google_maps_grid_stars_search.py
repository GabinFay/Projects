import requests
import os
import time

API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")

NEARBY_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

# Strasbourg bounding box (widened)
MIN_LAT, MAX_LAT = 48.5453, 48.5994
MIN_LNG, MAX_LNG = 7.7235, 7.7836

GRID_SIZE = 6
RADIUS = 750

def generate_grid():
    lat_step = (MAX_LAT - MIN_LAT) / GRID_SIZE
    lng_step = (MAX_LNG - MIN_LNG) / GRID_SIZE
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            lat = MIN_LAT + (i + 0.5) * lat_step
            lng = MIN_LNG + (j + 0.5) * lng_step
            yield lat, lng

def search_places(lat, lng):
    params = {
        'location': f'{lat},{lng}',
        'radius': RADIUS,
        'key': API_KEY
    }
    
    all_results = []
    while True:
        response = requests.get(NEARBY_SEARCH_URL, params=params)
        data = response.json()
        
        if 'error_message' in data:
            print(f"Error: {data['error_message']}")
            break
        
        all_results.extend(data.get('results', []))
        
        if 'next_page_token' not in data:
            break
        
        params['pagetoken'] = data['next_page_token']
        time.sleep(2)
    
    return all_results

all_places = []
for lat, lng in generate_grid():
    print(f"Searching at coordinates: {lat}, {lng}")
    places = search_places(lat, lng)
    all_places.extend(places)

unique_places = {place['place_id']: place for place in all_places}.values()
sorted_places = sorted(unique_places, key=lambda x: x.get('user_ratings_total', 0), reverse=True)

print("\nTop 20 places with the most reviews:")
for place in sorted_places[:20]:
    print(f"{place['name']} - {place.get('user_ratings_total', 'N/A')} reviews")
    print(f"  Location: {place['geometry']['location']}")
    print(f"  Types: {place['types']}")
    print()

print(f"\nTotal unique places found: {len(unique_places)}")

# Check specifically for Place Kléber
kleber_found = any(place['name'].lower().startswith('place kléber') for place in unique_places)
print(f"\nPlace Kléber found: {'Yes' if kleber_found else 'No'}")

if not kleber_found:
    print("\nSearching specifically for Place Kléber:")
    kleber_params = {
        'location': '48.5834,7.7456',  # Approximate coordinates of Place Kléber
        'radius': 100,
        'keyword': 'Place Kléber',
        'key': API_KEY
    }
    kleber_response = requests.get(NEARBY_SEARCH_URL, params=kleber_params)
    kleber_data = kleber_response.json()
    if kleber_data.get('results'):
        kleber_place = kleber_data['results'][0]
        print(f"Found: {kleber_place['name']} - {kleber_place.get('user_ratings_total', 'N/A')} reviews")
        print(f"  Location: {kleber_place['geometry']['location']}")
        print(f"  Types: {kleber_place['types']}")
    else:
        print("Place Kléber not found even in specific search.")