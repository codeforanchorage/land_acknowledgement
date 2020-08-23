'''
Classes to handle responses based on the type of location returned from the geocoder.
In general we are hoping for place and postal code locations. Larger areas like states
and countries don't make sense and the classes should respond appropirately.
'''

MORE_INFO_LINK = "bit.ly/landackn"
SUFFIX = f"More info: {MORE_INFO_LINK}"


class GenericResponse():
    def __init__(self, query, location, geodata):
        self.location = location
        self.geodata = geodata
        self.query = query

    def land_string(self, lands):
        '''Converts lists of lands into string sent to user'''
        names = [land['name'] for land in lands]
        if len(lands) == 1:
            land_string = names[0]
        elif len(lands) == 2:
            land_string = ' and '.join(names)
        else:
            all_but_last = ', '.join(names[:-1])
            land_string = f'{all_but_last}, and {names[-1]}'

        return land_string

    def __str__(self):
        return f"Sorry, I don't have information about {self.query}.\n{SUFFIX}"


class TooBigResponse(GenericResponse):
    '''Respond to places like countries and states.'''
    def __str__(self):
        place_type = self.location['place_type'][0]
        place_name = self.location['text']
        return (
            f"A {place_type} like {place_name} is a little too big for this service. "
            f"Try sending a city and state.\n{SUFFIX}"
        )


class PoiResponse(GenericResponse):
    '''Response for points of interest.'''
    def __str__(self):
        place_name = self.query
        return (
            f"I don't know how to find information about {place_name}. "
            f"Try sending a city and state.\n{SUFFIX}"
        )


class LocationResponse(GenericResponse):
    '''Base class for repsonses that hit the geocoder.'''
    def __str__(self):
        lands = self.geodata.native_land_from_point(*self.location['center'])
        if not lands:
            return super().__str__()
        context = {item['id'].partition('.')[0]: item['text'] for item in self.location['context']}
        land_string = self.land_string(lands)
        return self.response_from_area(land_string, context)


class PostalCodeResponse(LocationResponse):
    '''Response for zip codes.'''
    def response_from_area(self, land_string, context):
        area = self.location['text']
        return f"In the area of {area} you are on {land_string} land.\n{SUFFIX}"


class PlaceResponse(LocationResponse):
    '''Response for cities and towns.'''
    def response_from_area(self, land_string, context):
        place = self.location['text']
        if 'region' in context:
            place = ', '.join([place, context.get('region')])
        return f"In {place} you are on {land_string} land.\n{SUFFIX}"


class AddressResponse(LocationResponse):
    '''Response for addresses'''
    def response_from_area(self, land_string, context):
        street = self.location['text']
        if 'place' in context:
            street = ', '.join([street, context.get('place'), context.get('region')])
        return f"On {street} you are on {land_string} land.\n{SUFFIX}"
