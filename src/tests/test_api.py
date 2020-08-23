'''
The easiest way to run tests without needing to install dependencies is from
within the docker container. Once the container is running with:
> docker-compose up
exec into the container and run tests
> docker exec -it landak_web sh
> python -m pytest
'''
from unittest.mock import patch
import pytest
from falcon import testing
from app.web import create_app
from xml.dom import minidom
from app.responses import SUFFIX


@pytest.fixture
def good_geo_location():
    return {
        'type': 'FeatureCollection',
        'query': ['anchorage', 'ak'],
        'features': [{
                'id': 'place.19268916718032980',
                'type': 'Feature',
                'place_type': ['place'],
                'relevance': 1,
                'properties': {'wikidata': 'Q39450'},
                'text': 'Anchorage',
                'place_name': 'Anchorage, Alaska, United States',
                'bbox': [-159.516899997364, 55.8944109861981, -141.00268595324, 70.6124380154738],
                'center': [-149.8949, 61.2163],
                'geometry': {'type': 'Point', 'coordinates': [-149.8949, 61.2163]},
                'context': [
                    {
                        'id': 'region.19678797538778630',
                        'wikidata': 'Q797',
                        'short_code': 'US-AK',
                        'text': 'Alaska'
                    },
                    {
                        'id': 'country.19678805456372290',
                        'short_code': 'us',
                        'wikidata': 'Q30',
                        'text': 'United States'
                    }]
        }]
    }


class FakeResp:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data


def get_message_from_xml(xml_string):
    '''Just a little help to deal with twilio's xml format'''
    xmldoc = minidom.parseString(xml_string)
    itemlist = xmldoc.getElementsByTagName('Message')
    return itemlist[0].firstChild.data


@pytest.fixture()
def client():
    return testing.TestClient(create_app())


@patch('app.geocode.requests.get')
def test_404_location(geolocate, client):
    '''It should communicate that the location can't be found'''
    geolocate.return_value = FakeResp({'message': 'Not Found'}, 404)
    result = client.simulate_post('/', params={'Body': "Blah"})
    assert get_message_from_xml(result.text) == "I could not find the location: Blah"


@patch('app.geocode.requests.get')
def test_unknown_location(geolocate, client):
    '''It should communicate that the location can't be found'''
    geolocate.return_value = FakeResp({'features': []}, 200)
    result = client.simulate_post('/', params={'Body': "Blah"})
    assert get_message_from_xml(result.text) == "I could not find the location: Blah"


@patch('app.geocode.requests.get')
@patch('app.web.GeoData.native_land_from_point')
def test_unfound_acknowledgement(from_point, query_location, good_geo_location, client):
    '''It should respond with help text when there's no native land for a point'''
    query_location.return_value = FakeResp(good_geo_location, 200)
    from_point.return_value = []

    result = client.simulate_post('/', params={'Body': "Anchorage, AK"})
    assert get_message_from_xml(result.text) == f"Sorry, I don't have information about Anchorage, AK.\n{SUFFIX}"


@patch('app.geocode.requests.get')
@patch('app.web.GeoData.native_land_from_point')
def test_single_result(from_point, query_location, good_geo_location, client):
    '''It should respond with a single result when there's only one'''
    print(good_geo_location)

    query_location.return_value = FakeResp(good_geo_location, 200)
    from_point.return_value = [{'name': 'Chamorro'}]
    result = client.simulate_post('/', params={'Body': "Anchorage, AK"})
    assert get_message_from_xml(result.text) == f'In Anchorage, Alaska you are on Chamorro land.\n{SUFFIX}'


@patch('app.geocode.requests.get')
@patch('app.web.GeoData.native_land_from_point')
def test_two_results(from_point, query_location, good_geo_location, client):
    '''It should respond with a two results when there's two results'''
    query_location.return_value = FakeResp(good_geo_location, 200)
    from_point.return_value = [{'name': 'Cowlitz'}, {'name': 'Clackamas'}]
    result = client.simulate_post('/', params={'Body': "Anchorage, AK"})
    assert get_message_from_xml(result.text) == f'In Anchorage, Alaska you are on Cowlitz and Clackamas land.\n{SUFFIX}'


@patch('app.geocode.requests.get')
@patch('app.web.GeoData.native_land_from_point')
def test_multiple_results(from_point, query_location, good_geo_location, client):
    '''It prefers the Oxford comma'''
    query_location.return_value = FakeResp(good_geo_location, 200)
    from_point.return_value = [{'name': 'Duwamish'}, {'name': 'Coast Salish'}, {'name': 'Suquamish'}]
    result = client.simulate_post('/', params={'Body': "Anchorage, AK"})
    assert get_message_from_xml(result.text) == f'In Anchorage, Alaska you are on Duwamish, Coast Salish, and Suquamish land.\n{SUFFIX}' # noqa E501
