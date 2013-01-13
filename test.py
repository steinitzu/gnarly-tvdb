import logging

from gnarlytvdb import TVDB
from gnarlytvdb import EpisodeNotFoundError, SeasonNotFoundError, SeriesNotFoundError

log = logging.getLogger('thetvdb')
log.setLevel(logging.DEBUG)

# t = thetvdb.TVDB()

# series = t.get_series_id('the king of queens')
#data = t.get_full_series(series)

import unittest


class TestWithCacheEN(unittest.TestCase):
    
    def setUp(self):
        self.tvdb = TVDB(
            cache='/tmp/thetvdbtest',
            get_first=True,
            cache_max_age=9000,
            language='en'
            )
        self.seinid=79169            
        self.seinimdb='tt0098904'

    def test_get_series(self):
        series = self.tvdb.get_series('seinfeld')
        self.assertEqual(series['id'], self.seinid)
        with self.assertRaises(SeriesNotFoundError):
            self.tvdb.get_series('This show does not exists does it really?')
        series = self.tvdb.get_series(self.seinimdb, imdb=True)                

    def test_get_ep_from_series(self):
        series = self.tvdb.get_series('seinfeld')
        ep = series.season(3).episode(14)
        self.assertEqual(ep['episodename'], 'The Pez Dispenser')
        with self.assertRaises(EpisodeNotFoundError):
            series.season(3).episode(32)
        with self.assertRaises(SeasonNotFoundError):
            series.season(10).episode(5)        

    def test_getitem(self):
        series = self.tvdb['seinfeld']
        series = self.tvdb[self.seinimdb, 'imdb']

unittest.main(verbosity=2)