#!/usr/bin/env/python
#encoding:utf-8

import logging

from gnarlytvdb import TVDB
from gnarlytvdb import EpisodeNotFoundError, SeasonNotFoundError, SeriesNotFoundError

log = logging.getLogger('thetvdb')
log.setLevel(logging.DEBUG)

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

    def test_seriesdict(self):
        """
        Check if fetched series is really in series dict.
        """
        series = self.tvdb.get_series('seinfeld')
        assert self.tvdb.sid_series[series['id']] == series

    def test_dvd_order(self):
        series = self.tvdb.get_series('seinfeld')
        ep3 = series.season(2).episode(3)
        dvd3 = series.season(2, order='dvd').episode(3)
        assert ep3['episodename'] == 'The Jacket'
        assert dvd3['episodename'] == 'The Busboy'

    def test_unicode(self):
        sname = u'ástríður'
        series = self.tvdb[sname]
        assert series['seriesname'].lower() == sname

    def test_get_many_series(self):
        self.tvdb.get_first = False
        l = self.tvdb['scrubs']
        assert isinstance(l, list)
        assert len(l) > 1


unittest.main(verbosity=2)
