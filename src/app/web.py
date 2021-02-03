import json
import falcon
from twilio.twiml.messaging_response import MessagingResponse
from .db import GeoData
from .geocode import geolocate, LocationNotFound
from .responses import (
    TooBigResponse,
    PostalCodeResponse,
    PlaceResponse,
    AddressResponse,
    PoiResponse,
    GenericResponse
)


class Make_TwilML:
    def process_response(self, req, resp, resource, req_succeeded):
        '''Post-request middleware to turn the response into twilio's XML format'''
        twil_resp = MessagingResponse()
        twil_resp.message(resp.body)
        resp.body = str(twil_resp)


def check_empty_input(req, resp, resource, params):
    '''Hook to intercept empty messages or messages with predictable greetings'''
    greetings = {'hello', 'hi', 'help'}
    query = req.get_param('Body') and req.get_param('Body').strip()

    if not query or query.lower() in greetings:
        body = "Hello. Please tell me the town and state you are in. For example, 'Anchorage, AK'"
        raise falcon.HTTPStatus(falcon.HTTP_200, body=body)
    elif len(query) < 3:
        body = "Hmm, that seems a little vague. Try sending a city and state such as 'Anchorage, AK'"
        raise falcon.HTTPStatus(falcon.HTTP_200, body=body)


class LandResource(object):
    def __init__(self):
        self.geodata = None
        self.type_dispatch = {
            'country': TooBigResponse,
            'region': TooBigResponse,
            'postcode': PostalCodeResponse,
            'district': TooBigResponse,
            'place': PlaceResponse,
            'locality': PlaceResponse,
            'neighborhood': PlaceResponse,  # these might be to vauge to handle
            'address': AddressResponse,
            'poi': PoiResponse
        }

    @falcon.before(check_empty_input)
    def on_post(self, req, resp):
        print(json.dumps(req.params))

        if self.geodata is None:
            self.geodata = GeoData()

        query = req.get_param('Body').strip()

        try:
            location = geolocate(query)
        except LocationNotFound:
            raise falcon.HTTPStatus(falcon.HTTP_200, body=f"I could not find the location: {query}")
        except Exception as e:
            print(e)
            raise falcon.HTTPStatus(falcon.HTTP_200, body="Sorry, I having some technical trouble right now.")

        place_type = location['place_type'][0]
        response_class = self.type_dispatch.get(place_type, GenericResponse)
        response = response_class(query, location, self.geodata)

        resp.body = str(response)


def create_app():
    app = falcon.API(media_type=falcon.MEDIA_XML, middleware=[Make_TwilML()])
    app.req_options.auto_parse_form_urlencoded = True
    resource = LandResource()
    app.add_route('/', resource)
    return app


app = create_app()
