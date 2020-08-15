import os
import re
import logging
from functools import wraps
import psycopg2
from psycopg2.extras import DictCursor
from tenacity import retry, wait_exponential, stop_after_attempt

logger = logging.getLogger('gunicorn.error')


def retry_connection(f):
    '''Decorator to allow retrying connection when the DB drops the connection'''
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential()
    )
    @wraps(f)
    def wrapper(geoObj, *args, **kwds):
        try:
            return f(geoObj, *args, **kwds)
        except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
            logger.warning(e)
            geoObj.reconnect()
            raise e
    return wrapper


class GeoData():
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', default='postgresql://postgres:postgres@postgres')
        self._connection = None

    def connect(self):
        if self._connection is None:
            try:
                self._connection = psycopg2.connect(self.db_url)
            except psycopg2.DatabaseError as e:
                logger.error(e)
                raise e

    def reconnect(self):
        self._connection = None
        self.connect()

    @property
    def connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    @retry_connection
    def query_location(self, location):
        '''
        Find a place and coordinates using fuzzy name matching.
        '''
        if re.match(r'^\d{5}(-\d{4})?$', location):
            return self.query_zip(location)

        # To normalize variations like `Anchorage ak`, `Anchorage, Ak`, `Anchorage - AK`
        # this concatenates the name and removes non-word characters which matches an index on
        # postgres. If this goes beyond US names, this will need to change.
        smushed_name = re.sub(r'\W+', '', location).upper()

        query = '''
            SELECT city, state, state_code, latitude, longitude from geo
            WHERE regexp_replace(UPPER(city || state), '\\W+', '', 'g') = %(s)s
            OR regexp_replace(UPPER(city || state_code), '\\W+', '', 'g') = %(s)s
            LIMIT 1
            '''
        with self.connection.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, {'s': smushed_name})
            return cur.fetchone()

    @retry_connection
    def query_zip(self, zipcode):
        '''
        Find a place and coordinates from zip code. The DB only has 5-digit codes
        This will strip off the plus-4 if it's there.
        '''
        zipcode, *ext = zipcode.split('-')

        query = '''
            SELECT state, city, latitude, longitude from zipcode
            WHERE zipcode = %s
            LIMIT 1
            '''
        with self.connection.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (zipcode, ))
            return cur.fetchone()

    @retry_connection
    def native_land_from_point(self, lat, lon):
        '''
        Lookup native land that contains point.
        Point is interpetered as srid 4326 (WGS 84 : https://spatialreference.org/ref/epsg/4326/)
        '''
        query = '''
        SELECT name, description
        FROM indigenousterritories
        WHERE ST_Contains(wkb_geometry,ST_GeometryFromText('POINT( %s %s)', 4326) )
        GROUP BY name, description
        ;
        '''
        with self.connection.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (lon, lat))
            return cur.fetchall()
