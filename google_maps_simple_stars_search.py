import requests
import os
import time

# Get API key from environment variable
API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")

# Get API key from environment variable
URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

# Coordinates for the center of Strasbourg
STRASBOURG_LAT = 48.5734053
STRASBOURG_LNG = 7.7521113

def fetch_places(lat, lng, radius):
    params = {
        'location': f'{lat},{lng}',
        'radius': radius,
        'key': API_KEY
    }
    
    all_places = []
    
    while True:
        response = requests.get(URL, params=params)
        data = response.json()
        
        if 'error_message' in data:
            print(f"Error: {data['error_message']}")
            break
        
        all_places.extend(data.get('results', []))
        
        if 'next_page_token' not in data:
            break
        
        params['pagetoken'] = data['next_page_token']
        time.sleep(2)  # Wait before making the next request
    
    return all_places

# Fetch places in multiple smaller radii to ensure coverage
radii = [1000, 2000, 3000, 4000, 5000]
all_places = []

for radius in radii:
    places = fetch_places(STRASBOURG_LAT, STRASBOURG_LNG, radius)
    all_places.extend(places)

# Remove duplicates based on place_id
unique_places = {place['place_id']: place for place in all_places}.values()

# Print places with more than 2000 reviews
for place in unique_places:
    if place.get('user_ratings_total', 0) > 2000:
        print(f"{place['name']} - {place['user_ratings_total']} reviews")
