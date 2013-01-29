# gnarlytvdb (python) #

This is yet another python interface to [thetvdb.com](http://thetvdb.com) programmer's api. 
Its aim is to be fast, simple to use and easy to understand.

## Features ##
* String values from TVDB are (mostly) converted to the appropriate python datatypes
* In memory and on disk caching
* Look up a series by imdb id
* Supports aired and DVD ordering for seasons and episodes


## Install from pypi ##
GnarlyTVDB is on pypi and can be easily install usind pip.
If you don't have pip, see install instructions [here](http://www.pip-installer.org/en/latest/installing.html) or see if it is available through your distro's package management system (e.g. apt-get install python-pip).
After you have installed pip you can go ahead and install gnarlytvdb with the following command:  

    pip install gnarlytvdb
    
(you may need to add sudo in front of that command)  
That's it.

## Install from source ##
If you prefer to get the latest changes from the source repo, here is how.

Start by cloning the repo.

    cd /tmp
    git clone git://github.com/steinitzu/gnarly-tvdb.git
    
cd to the projects root folder

    cd gnarly-tvdb
    
now install (you may need to add `sudo` in front of the next command)

    python setup.py install

That's it!
Now lets move on and see how to use this thing.


## Basic usage ##
The main component of gnarlytvdb is the `TVDB` class. 
Note if you don't already have a tvdb api key for your application, you can register for one [here](http://thetvdb.com/?tab=apiregister).

So lets start by opening a TVDB instance.

    >> from gnarlytvdb import TVDB
    >> tv = TVDB(api_key='my_api_key')
    
Other available arguments for `TVDB` are documented in the class' docstring.

Now we can get our selves some data from thetvdb.

    >> series = tv['seinfeld']
    
or

    >> series = tv.get_series('seinfeld')
    
Series becomes an object of the `Series` class.
It is a dict based class and each instance of it will represent a <Series> XML element from thetvdb XML api for the requested series. Keys are converted to lower case however.

When you fetch a series using the above mentioned methods, all the child episode text data is fetched as well.
So, say you want to see the name of episode 5x4

    >> print series.season(5).episode(4)['episodename']
    The sniffing Accountant
    
Or you want to see when Seinfeld first aired

    >> print series['firstaired']
    1990-05-31

It is also possible to get episodes in their DVD release order by setting the `order` argument to 'dvd'.
Example:

    >> print series.season(2).episode(12)['episodename']
    The Busboy
    >> print series.season(2, order='dvd').episode(12)['episodename']
    The Revenge    
    


Please feel free to contact me with any questions, comments, bug reports, hatemail, loveletters, etc, either in the project's bugtracker https://github.com/steinitzu/gnarly-tvdb/issues or at steinitzu@gmail.com 


* TODO: Implement actors and banners
