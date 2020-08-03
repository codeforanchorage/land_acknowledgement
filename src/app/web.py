from urllib.parse import parse_qs
import falcon
from twilio.twiml.messaging_response import MessagingResponse
from .db import GeoData
from .logger import logger


class LandResource(object):
    def on_get(self, req, resp):
        resp.body = (
            'Nothing to see here.'
        )

    def on_post(self, req, resp):
        twil_resp = MessagingResponse()
        resp.set_header('Content-Type', 'text/html; charset=UTF-8')

        if req.content_length == 0:
            twil_resp.message(f"Please tell me the town and state you are in. For example, 'Anchorage, AK'")
            resp.body = str(twil_resp)
            return

        data = req.stream.read()
        params = parse_qs(data.decode('utf-8'))
        logger.info(params)

        query = params['Body'][0].strip()

        if not query:
            twil_resp.message(f"Please tell me the town and state you are in. For example, 'Anchorage, AK'")
            resp.body = str(twil_resp)
            return

        geodata = GeoData()
        geodata.connect()

        location = geodata.query_location(query)

        if location is None:
            twil_resp.message(f"I could not find the location: {query}")
            resp.body = str(twil_resp)
            return

        r = geodata.native_land_from_point(location['latitude'], location['longitude'])

        if r is None:
            twil_resp.message(f"Sorry, I could not find anything about {location['city']}, {location['state']}")
            resp.body = str(twil_resp)
            return

        twil_resp.message(f"In {location['city']}, {location['state']} you are on {r['name']} land")
        resp.body = str(twil_resp)


app = falcon.API()

resource = LandResource()

app.add_route('/', resource)
