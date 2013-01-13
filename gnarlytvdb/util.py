#!/usr/bin/env/python
#encoding:utf-8

import re, os, md5, logging
from tempfile import gettempdir

import httplib2

def sanitize(string):
    """
    Clean gunk from a string like a series name.
    Removes most non \w characters and sends it back in lowercase.
    """
    return string.lower()

def get_cache_dir():
    tmp = gettempdir()
    return os.path.join(tmp, 'thetvdb-cache')

re_url_scheme    = re.compile(r'^\w+://')
re_slash         = re.compile(r'[?/:|]+')
def safe_filename(filename):
    """Return a filename suitable for the cache.

    Strips dangerous and common characters to create a filename we
    can use to store the cache in.
    """

    try:
        if re_url_scheme.match(filename):
            if isinstance(filename,str):
                filename = filename.decode('utf-8')
                filename = filename.encode('idna')
            else:
                filename = filename.encode('idna')
    except UnicodeError:
        pass
    if isinstance(filename,unicode):
        filename=filename.encode('utf-8')
    filemd5 = md5.new(filename).hexdigest()
    filename = re_url_scheme.sub("", filename)
    filename = re_slash.sub(",", filename)

    # limit length of filename
    if len(filename)>80:
        filename=filename[:80]
    return ",".join((filename, filemd5))

def get_file_cache(cache_dir):
    cache_dir = cache_dir or get_cache_dir()
    fc = httplib2.FileCache(
        cache_dir,
        safe=safe_filename
        )
    return fc


    
