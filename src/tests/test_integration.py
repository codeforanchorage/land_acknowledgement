'''
The easiest way to run tests without needing to install dependencies is from
within the docker container. Once the container is running with. These test
depend on the local postgres instance.
> docker-compose up
exec into the container and run tests
> docker exec -it landak_web sh
> python -m pytest
'''
import pytest
from falcon import testing
from app.web import create_app
from xml.dom import minidom
from app.responses import SUFFIX


def get_message_from_xml(xml_string):
    '''Just a little help to deal with twilio's xml format'''
    xmldoc = minidom.parseString(xml_string)
    itemlist = xmldoc.getElementsByTagName('Message')
    return itemlist[0].firstChild.data


@pytest.fixture()
def client():
    return testing.TestClient(create_app())


def test_an_unknown_location(client):
    '''It should respond with help text when location can't be found'''
    result = client.simulate_post('/', params={'Body': "Blah"})
    assert get_message_from_xml(result.text) == f"Sorry, I don't have information about Blah.\n{SUFFIX}"


def test_known_greeting(client):
    '''It should respond with help text when location can't be found'''
    result = client.simulate_post('/', params={'Body': "Hello"})
    assert get_message_from_xml(result.text) == "Hello. Please tell me the town and state you are in. For example, 'Anchorage, AK'" # noqa E501


def test_empty_input(client):
    '''It should respond with help text when location can't be found'''
    result = client.simulate_post('/', params={'Body': ""})
    assert get_message_from_xml(result.text) == "Hello. Please tell me the town and state you are in. For example, 'Anchorage, AK'" # noqa E501


def test_known_location(client):
    '''It should respond land when location can be found'''
    result = client.simulate_post('/', params={'Body': "Minneapolis, MN"})
    assert get_message_from_xml(result.text) == f'In Minneapolis, Minnesota you are on Wahpekute and Očeti Šakówiŋ (Sioux) land.\n{SUFFIX}'  # noqa E501


def test_zipcode_location(client):
    '''It should respond with help text when location can't be found'''
    result = client.simulate_post('/', params={'Body': "99577"})
    assert get_message_from_xml(result.text) == f"In the area of 99577 you are on Dena'ina Ełnena land.\n{SUFFIX}"
