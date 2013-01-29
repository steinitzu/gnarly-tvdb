#!/usr/bin/env/python
#encoding:utf-8

from urllib import quote
from datetime import datetime
from cStringIO import StringIO
from zipfile import ZipFile
import logging, sys
from collections import OrderedDict

import httplib2
import xmltodict

from .util import get_file_cache, sanitize

def make_log():
    log = logging.getLogger('thetvdb')
    format = logging.Formatter(
        '%(levelname)s:%(asctime)s:%(funcName)s:%(message)s'
        )
    sh = logging.StreamHandler()
    sh.setFormatter(format)
    log.addHandler(sh)    
make_log()

log = logging.getLogger('thetvdb')
DEFAULT_API_KEY = '29E8EC8DF23A5918'

class TheTVDBException(Exception): 
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args)
        for k,v in kwargs.iteritems():
            self.__setattr__(k,v)
class EmptyXMLError(TheTVDBException): pass
class TVDBDataError(TheTVDBException): pass
class TVDBConnectError(TheTVDBException): 
    errno = None    
class InvalidArgumentError(TheTVDBException): pass
class SeriesNotFoundError(TheTVDBException): pass
class SeasonNotFoundError(TheTVDBException): pass
class EpisodeNotFoundError(TheTVDBException): pass
class ItemExistsError(TheTVDBException): pass

def _clean_value(key, value):
    """
    _clean_value(key, value) -> value
    Clean and convert to tvdb data to the right type.
    E.g. datefields are converted to date types, integer to ints and such.
    """
    if value is None or value == '':
        return
    dates = ('firstaired',)
    ints = (
        'id', 'seasonid', 
        'seasonnumber', 'episodenumber',
        'dvd_season', 'absolute_number',        
        )
    floats = (
        'dvd_episodenumber'
        )
    if key in dates:
        return datetime.strptime(value, '%Y-%m-%d').date()
    elif key in ints:
        return int(value)
    elif key in floats:
        return float(value)
    else:
        return value

class Item(dict):
    def __init__(self, **kwargs):
        self.update(kwargs)
        self.init()

    def init(self):
        raise NotImplementedError()

    def update(self, d):
        for k,v in d.iteritems():
            if k == '#text': #junk key from xmltodict
                continue
            k = k.lower()
            super(Item, self).__setitem__(k,_clean_value(k, v))

    def __setitem__(self, key, value):
        raise TheTVDBException('Item is read-only')            
    
class Series(Item):

    def init(self):
        self.seasons = {} #seasonnum:Season
        self.dvd_seasons = {}

    def add_episode(self, ep):
        """
        Add given Episode to this Series.
        Seasons will be created implicitly.
        """
        #make da season
        ses = self._add_season(ep)
        dvdses = self._add_season(ep, dvd=True)        
        self._add_episode(ep, ses)
        self._add_episode(ep, dvdses, dvd=True)
        
    def _add_episode(self, ep, season, dvd=False):
        if dvd:
            epnum = ep['dvd_episodenumber']
        else:
            epnum = ep['episodenumber']
        ep.series = self
        season.episodes[epnum] = ep

    def _add_season(self, ep, dvd=False):
        """
        Make a Season object for given Episode and 
        add it to appropriate seasons dict.
        Resulting Season is returned.
        """
        if dvd:
            snum = ep['dvd_season']
            seasons = self.dvd_seasons
        else:
            snum = ep['seasonnumber']
            seasons = self.seasons
        if seasons.has_key(snum):
            return seasons[snum]
        else:
            s = Season(
                sasonnumber=snum,
                seasonid=ep['seasonid'],
                seriesid=ep['seriesid']
                )
            s.series = self
            seasons[snum] = s
            return s

    def season(self, seasonnum, order='aired'):
        """
        Get a Season by season number.
        `order` can be 'aired' or 'dvd' depending on the 
        desired season/episode ordering.
        Subsequent episodes will follow the order given here.
        """
        if order=='aired':
            seasons = self.seasons
        elif order == 'dvd':
            seasons = self.dvd_seasons
        try:
            return seasons[seasonnum]
        except KeyError:
            raise SeasonNotFoundError(
                'Season no %s does not exists' % seasonnum
                ), None, sys.exc_info()[2]            
        

class Season(Item):
    def init(self):
        self.episodes = {} #epnum:Episode
        self.series = None

    def episode(self, episodenum):        
        try:
            return self.episodes[episodenum]
        except KeyError as e:
            raise EpisodeNotFoundError(
                'Episode no %s does not exists' % episodenum
                ), None, sys.exc_info()[2]

class Episode(Item):    
    def init(self):
        self.season = None
        self.series = None

def add_to_series_dict(func):
    """
    A decorator function to add fetched series to dict.
    """
    def add(self, *args, **kwargs):
        s = func(self, *args, **kwargs)
        self.sid_series[s['id']] = s
        return s
    return add

class TVDB(object):
    #TODO: make these instance vars
    url_base = u'http://thetvdb.com'
    url_getseries = u'/api/GetSeries.php?seriesname=%(seriesname)s&language=%(language)s'
    url_getseriesbyimdb = u'/api/GetSeriesByRemoteID.php?imdbid=%(seriesname)s'
    __url_epinfo = u'/api/%(apikey)s/series/%(seriesname)s/all/%(language)s'
    url_epinfo = __url_epinfo+'.xml'
    url_epinfozip = __url_epinfo+'.zip'    

    _defs = {
       'api_key':None,
       'cache':True, 
       'get_first':True,
       'language':'en',
       'cache_max_age' : 86400, #'cache-control':'max-age' in seconds
       }       

    langs = {
        'da':10,
        'fi':11,
        'nl':13,
        'de':14,
        'it':15,
        'es':16,
        'fr':17,
        'pl':18,
        'hu':19,
        'el':20,
        'tr':21,
        'ru':22,
        'he':24,
        'ja':25,
        'pt':26,
        'zh':27,
        'cs':28,
        'sl':30,
        'hr':31,
        'ko':32,
        'en':7,
        'sv':8,
        'no':9,
        }

    def __init__(self, **kwargs):
        """
        Allowed keyword arguments:
        
        api_key=str
            Api key for your application.
            Get one here if you don't have one.
            http://thetvdb.com/?tab=apiregister            
            If None is passed, gnarlytvdb's default api key is used.

        cache=bool|path
            Can be either a bool or a path to a directory.
            If True, cache is stored in the default cache directory
            defined by `thetvdb.get_cache_dir()`
            default=%(cache)s
        
        get_first=bool
            If True, only the first result of a series lookup is returned.
            If False, a list of results is returned.        
            default=%(get_first)s

        language=str
            Requested language of show data. Default is English.
            See `langs` for available languages.
            Can also be set to 'all' meaning all languages will be searched.
            default=%(language)s

        cache_max_age=int
            The maximum age (in seconds) of a cached request 
            before it is re-fetched.
            This is sent as the 'cache-control':'max-age' 
            header with every http request to thetvdb.
            default=%(cache_max_age)s
        """        
        for k, v in self._defs.iteritems():
            try:
                self.__setattr__(k, kwargs[k])
            except KeyError:
                self.__setattr__(k, v)
        for opt in kwargs.iterkeys():
            if not self._defs.has_key(opt):
                raise InvalidArgumentError(
                    '%s is not a valid option for TVDB.' % opt
                    )
        if self.cache:
            if self.cache is True:
                #so we get the default dir
                self.cache=None
            self.cache = get_file_cache(self.cache)
        else: self.cache = None
        if not self.api_key:
            self.api_key = DEFAULT_API_KEY

        self.name_seriesid = {} #dict storing name:sid mappings
        self.sid_series = OrderedDict()
        self.http = httplib2.Http(cache=self.cache)
        self._reqheaders = {
            'cache-control':'max-age=%s' % self.cache_max_age
            }

    def _get_series_id(self, url, seriesname):
        xml = self._get_raw_data(url, seriesname)
        try:
            series = self._xml_to_series(xml)
        except EmptyXMLError:
            raise SeriesNotFoundError(
                'No series with name "%s" found on tvdb' % seriesname
                )
        if self.get_first:
            seriesid = series['id']
            self.name_seriesid[seriesname] = seriesid
            return seriesid
        else:
            return [s['id'] for s in series]            

    def get_series_id(self, seriesname, imdb=False):
        """
        Get a series id from thetvdb for the given `seriesname`.
        (or imdb id if `imdb` == True).
        If a result with the same name has already been fetched by this 
        instance, it will be retrieved from the `self.name_seriesid` dict.

        If `get_first` is False, this will return a list of series ids.
        """
        log.debug('Getting series id for: "%s"', seriesname)
        if imdb:
            url = self.url_getseriesbyimdb
        else:
            url = self.url_getseries
        seriesname = sanitize(seriesname)
        try:
            #see if we already fetched it
            seriesid = self.name_seriesid[seriesname]
            log.debug('Already got a series id for: %s' % seriesname)
        except KeyError:
            seriesid = self._get_series_id(url, seriesname)
        log.debug('Returning sid: %s', seriesid)
        return seriesid

    @add_to_series_dict
    def get_series_by_id(self, seriesid):
        """
        Fill the given `Series` object with episode info.
        """        
        try:
            return self.sid_series[seriesid]
        except KeyError:
            pass #not memcached
        url = self.url_epinfozip
        data = self._get_raw_data(url, seriesid)        
        #lang.xml, actors.xml, banners.xml
        #lang.xml has ['Data']['Series'] and ['Data']['Episode']
        xmld = self._extract_zip(StringIO(data))
        for k,v in xmld.iteritems():
            xmld[k] = self._xml_to_dict(v)
        series = Series(**xmld[self.language+'.xml']['Data']['Series'])
        epdicts = xmld[self.language+'.xml']['Data']['Episode']
        for epd in epdicts:
            ep = Episode(**epd)
            series.add_episode(ep)
        return series

    def get_series(self, seriesname, imdb=False):
        """
        get_series(seriesname, imdb=False) -> Series
        Get series with given `seriesname`.
        if imdb==True, `seriesname` will be treated as an imdb id.
        """        
        if not self.get_first:
            shows =  self._get_many_series(seriesname, imdb=imdb)
            log.debug(shows)
            return shows
        sid = self.get_series_id(seriesname, imdb=imdb)
        return self.get_series_by_id(sid)

    def _get_many_series(self, seriesname, imdb=False):
        """
        Used when `get_first` is False.
        Returns a list of Series.
        """
        shows = []
        sids = [s for s in self.get_series_id(seriesname, imdb=imdb)]
        for s in sids:
            shows.append(self.get_series_by_id(s))
        log.debug('sids: %s', sids)
        return shows
        

    def __getitem__(self, key):
        if isinstance(key,(int, long)):
            #it's a seriesid
            return self.get_series_by_id(key)
        elif isinstance(key, tuple) and len(key) == 2:
            imdbid, mod = key
            if mod == 'imdb':
                return self.get_series(imdbid, imdb=True)
            else:
                raise KeyError(
                    '"%s" is not a valid key modifier.' % mod
                    )
        else:
            return self.get_series(key)                    

    def _extract_zip(self, zipfile):
        """
        _extract_zip(zip file object OR path to zip file) -> dict
        Return a dict of raw xml data in following form:
        {'`language`.xml':xmldata, 'banners.xml':xmldata, 'actors.xml':xmldata}
        `language` being `self.language`.
        """
        zf = ZipFile(zipfile)
        d = {}
        for n in zf.namelist():
            d[n] = zf.read(n)
        return d

    def _xml_to_dict(self, xml):
        try:
            return xmltodict.parse(xml)
        except Exception as e:
            raise TVDBDataError(
                'Unable to parse XML data from thetvdb.\n'\
                +'This could just mean the data got corrupted along the tubes.'\
                +'In that case, repeating the request should fix the problem.'\
                +'Otherwise, plese send in a bug report '\
                +'with full details of the error.'
                ), None, sys.exc_info()[2]

    def _xml_to_series(self, xml):
        """
        Convert XML to Series object.
        """
        d = self._xml_to_dict(xml)
        d = d['Data']
        if isinstance(d, basestring):
            raise EmptyXMLError('Provided xml has no content.')
        shows = d['Series'] #list of dicts
        if self.get_first:
            if isinstance(shows, list):
                return Series(**shows[0])
            else:
                return Series(**shows)
        else:
            if isinstance(shows, list):                
                return [Series(**v) for v in shows]
            else:
                return [Series(**shows)]


    def _get_raw_data(self, url, series):
        """
        Get the raw xml or zip data from thetvdb.
        `url` should usually be one of this classes' members `url_...`
        `series` can be a series name, id or imdb id.
        """
        url = self._get_url(url, series)
        try:
            response = self.http.request(url, headers=self._reqheaders)
        except httplib2.ServerNotFoundError as e:
            raise TVDBConnectError(e.message), None, sys.exc_info()[2]
        rep = response[0]
        log.debug(
            'http-status:%s,content:%s', 
            rep['status'], 
            rep['content-type']
            )
        if int(rep['status']) >= 400:
            raise TVDBConnectError(
                'Failed to get "%s" from thetvdb. errno:%s' % (
                    series, rep['status']),
                rep['status']
                )        
        return response[1]

    def _get_url(self, url, series):
        """
        Format given data into given url and concat it to `url_base`.
        `series` can be a string seriesname, an imdb id or a tvdb series id.        
        """
        d = {
            'apikey' : self.api_key,
            'language' : self.language
            }
        if isinstance(series, basestring):
            d['seriesname'] = quote(series.encode('utf-8'))
        else:
            d['seriesname'] = series
        url = url % d        
        return self.url_base+url
