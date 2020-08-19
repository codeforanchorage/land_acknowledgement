import json
import falcon
from twilio.twiml.messaging_response import MessagingResponse
from .db import GeoData


class Make_TwilML:
    def process_response(self, req, resp, resource, req_succeeded):
        '''Post-request middleware to turn the response into twilio's XML format'''
        twil_resp = MessagingResponse()
        twil_resp.message(resp.body)
        resp.body = str(twil_resp)


def response_from_locations(location, lands):
    '''Converts lists of lands into string sent to user'''
    names = [land['name'] for land in lands]
    prefix = f"In {location['city']}, {location['state']} you are on"

    if len(lands) == 1:
        land_string = names[0]
    elif len(lands) == 2:
        land_string = ' and '.join(names)
    else:
        all_but_last = ', '.join(names[:-1])
        land_string = f'{all_but_last}, and {names[-1]}'

    return f'{prefix} {land_string} land.'


def check_empty_input(req, resp, resource, params):
    '''Hook to intercept empty messages or messages with predictable greetings'''
    greetings = {'hello', 'hi', 'help'}
    query = req.get_param('Body') and req.get_param('Body').strip()

    if not query or query.lower() in greetings:
        body = "Hello. Please tell me the town and state you are in. For example, 'Anchorage, AK'"
        raise falcon.HTTPStatus(falcon.HTTP_200, body=body)


class LandResource(object):
    def __init__(self):
        self.geodata = None

    @falcon.before(check_empty_input)
    def on_post(self, req, resp):
        print(json.dumps(req.params))

        if self.geodata is None:
            self.geodata = GeoData()

        query = req.get_param('Body').strip()

        location = self.geodata.query_location(query)
        if location is None:
            raise falcon.HTTPStatus(falcon.HTTP_200, body=f"I could not find the location: {query}")

        r = self.geodata.native_land_from_point(location['latitude'], location['longitude'])

        if not r:
            body = f"Sorry, I could not find anything about {location['city']}, {location['state']}."
            raise falcon.HTTPStatus(falcon.HTTP_200, body=body)

        resp.body = response_from_locations(location, r)


def create_app():
    app = falcon.API(media_type=falcon.MEDIA_XML, middleware=[Make_TwilML()])
    app.req_options.auto_parse_form_urlencoded = True
    resource = LandResource()
    app.add_route('/', resource)
    return app


app = create_app()
