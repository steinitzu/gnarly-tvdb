# thetvdb (python) #

A simple python interface to [thetvdb.com](http://thetvdb.com) programmer's api.

## Install from source ##

Start by cloning the repo.
`cd /tmp`
`git clone git://github.com/steinitzu/thetvdb.git`
cd to the projects root folder
`cd thetvdb`
now install (you may need to add `sudo` in front of the next command)
`python setup.py install`

That's it!
Now lets move on and see how to use this thing.


## Basic usage ##
    from thetvdb.thetvdb import TVDB
    tv = TVDB(api_key='my_api_key')
    series = tv['seinfeld']
    season = series.season(5)
    episode = season.episode(7)

`Series`, `Season` and `Episode` are all dict based classes used as containers for TV show data.
They will have all the keys available on thetvdb.


* TODO: Make this readme more useful
* TODO: Implement actors and banners
