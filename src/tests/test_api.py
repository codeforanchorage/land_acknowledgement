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


def get_message_from_xml(xml_string):
    '''Just a little help to deal with twilio's xml format'''
    xmldoc = minidom.parseString(xml_string)
    itemlist = xmldoc.getElementsByTagName('Message')
    return itemlist[0].firstChild.data


@pytest.fixture()
def client():
    return testing.TestClient(create_app())


@patch('app.web.GeoData.query_location')
def test_unknown_location(query_location, client):
    '''It should respond with help text when location can't be found'''
    query_location.return_value = None
    result = client.simulate_post('/', params={'Body': "Sometown, ak"})
    assert get_message_from_xml(result.text) == 'I could not find the location: Sometown, ak'


@patch('app.web.GeoData.query_location')
@patch('app.web.GeoData.native_land_from_point')
def test_unfound_acknowledgement(from_point, query_location, client):
    '''It should respond with help text when there's no native land for a point'''
    query_location.return_value = {'city': 'Paris', 'state': 'France', 'latitude': 45.928, 'longitude': -67.56}
    from_point.return_value = []

    result = client.simulate_post('/', params={'Body': "Paris, France"})
    assert get_message_from_xml(result.text) == 'Sorry, I could not find anything about Paris, France.'


@patch('app.web.GeoData.query_location')
@patch('app.web.GeoData.native_land_from_point')
def test_single_result(from_point, query_location, client):
    '''It should respond with a single result when there's only one'''
    query_location.return_value = {'city': 'Adacao', 'state': 'Guam', 'latitude': 45.928, 'longitude': -67.56}
    from_point.return_value = [{'name': 'Chamorro'}]
    result = client.simulate_post('/', params={'Body': "Adacao, gu"})
    assert get_message_from_xml(result.text) == 'In Adacao, Guam you are on Chamorro land.'


@patch('app.web.GeoData.query_location')
@patch('app.web.GeoData.native_land_from_point')
def test_two_results(from_point, query_location, client):
    '''It should respond with a two results when there's two results'''
    query_location.return_value = {'city': 'Portland', 'state': 'Oregon', 'latitude': 45.928, 'longitude': -67.56}
    from_point.return_value = [{'name': 'Cowlitz'}, {'name': 'Clackamas'}]
    result = client.simulate_post('/', params={'Body': "Portland, or"})
    assert get_message_from_xml(result.text) == 'In Portland, Oregon you are on Cowlitz and Clackamas land.'


@patch('app.web.GeoData.query_location')
@patch('app.web.GeoData.native_land_from_point')
def test_multiple_results(from_point, query_location, client):
    '''It prefers the Oxford comma'''
    query_location.return_value = {'city': 'Seattle', 'state': 'Washington', 'latitude': 45.928, 'longitude': -67.56}
    from_point.return_value = [{'name': 'Duwamish'}, {'name': 'Coast Salish'}, {'name': 'Suquamish'}]
    result = client.simulate_post('/', params={'Body': "Seattle, wa"})
    assert get_message_from_xml(result.text) == 'In Seattle, Washington you are on Duwamish, Coast Salish, and Suquamish land.' # noqa E501
