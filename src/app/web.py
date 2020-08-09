import falcon
from twilio.twiml.messaging_response import MessagingResponse
from .db import GeoData


def make_twilML(req, resp, resource):
    twil_resp = MessagingResponse()
    twil_resp.message(resp.body)
    resp.body = str(twil_resp)


@falcon.after(make_twilML)
class LandResource(object):
    def __init__(self):
        self.geodata = None

    def on_get(self, req, resp):
        resp.body = (
            'Nothing to see here.'
        )

    def on_post(self, req, resp):
        print(req.params)
        if self.geodata is None:
            self.geodata = GeoData()
            self.geodata.connect()

        query = req.get_param('Body')

        if not query:
            resp.body = "Please tell me the town and state you are in. For example, 'Anchorage, AK'"
            return

        location = self.geodata.query_location(query)

        if location is None:
            resp.body = f"I could not find the location: {query}"
            return

        r = self.geodata.native_land_from_point(location['latitude'], location['longitude'])

        if r is None:
            resp.body = f"Sorry, I could not find anything about {location['city']}, {location['state']}"
            return

        resp.body = f"In {location['city']}, {location['state']} you are on {r['name']} land."


app = falcon.API(media_type=falcon.MEDIA_XML)

app.req_options.auto_parse_form_urlencoded = True
resource = LandResource()

app.add_route('/', resource)
