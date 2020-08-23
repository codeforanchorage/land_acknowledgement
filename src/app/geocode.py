import os
import requests


class ConfigurationError(Exception):
    pass


class APIError(Exception):
    pass


class LocationNotFound(Exception):
    pass


API_BASE = 'https://api.mapbox.com/geocoding/v5/mapbox.places/'
MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')

if MAPBOX_TOKEN is None:
    raise ConfigurationError("The env MAPBOX_TOKEN is missing from the environment.")

'''
Things that can go wrong with user input:
Blank input — check before querrying
Too short - can a query shorted than three characters ever be meaningful
Too broad - 'Canada' can't provide a meaningful result
'''


def geolocate(raw_str):
    query = {
        'access_token': MAPBOX_TOKEN,
        'type': 'place'
    }
    url = API_BASE + raw_str + '.json'
    resp = requests.get(url, params=query)
    data = resp.json()

    if resp.status_code == 404:
        # 404 is returned when the query fails to find anything
        raise LocationNotFound
    elif resp.status_code != 200:
        raise APIError(data.get('message'))

    return location_from_collection(data)


def location_from_collection(json_data):
    '''
    Returns the best feature from the collection of features
    returned by api. Best is determined by sorting by relevance then type in
    a way that favors places over less desireable results like POI.
    Raises LocationNotFound if the API returns an empty collection.
    '''

    priorities = {
        'place': 10,
        'postcode': 10,
        'locality': 9,
        'address': 8,
        'region': 7,
        'country': 6,
        'district': 5,
        'neighborhood': 5,
        'poi': 4
    }

    features = json_data['features']
    if len(features) == 0:
        raise LocationNotFound("Not found")
    return max(features, key=lambda f: (f['relevance'], priorities.get(f['place_type'][0], 0)))
