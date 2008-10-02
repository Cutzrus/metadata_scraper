## Copyright (c) 2006 Nathan R. Yergler, Creative Commons

## Permission is hereby granted, free of charge, to any person obtaining
## a copy of this software and associated documentation files (the "Software"),
## to deal in the Software without restriction, including without limitation
## the rights to use, copy, modify, merge, publish, distribute, sublicense,
## and/or sell copies of the Software, and to permit persons to whom the
## Software is furnished to do so, subject to the following conditions:

## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.

## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
## DEALINGS IN THE SOFTWARE.

import os
import sys
import gc
import rdfadict
import urlparse
import logging
import urllib2

import web
import simplejson as json

from decorator import decorator
from support import LOG

if sys.version < (2,5):
    # import set support
    from sets import Set as set

FOLLOW_PREDICATES = (
     'http://www.w3.org/1999/02/22-rdf-syntax-ns#seeAlso',
     'http://rdfs.org/sioc/ns#has_owner',
     )

urls = (
    '/triples', 'Triples',
    '/scrape',  'Scrape',
    )

class LogResult(object):
    """Log the result of a call to a given Logger object."""
    def __new__(cls, log, level=logging.INFO):
        self = super(LogResult, cls).__new__(cls)
        self._log = log
        self._level = level
    
        return self

    def call(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        self._log.log(self._level, result)

        return result

LogResult = decorator(LogResult)

class ScrapeRequestHandler(object):

    def _load_source(self, url, subjects=None, sink=None):

        parser = rdfadict.RdfaParser() 
	if subjects is None: subjects = []

        try:
            # load the specified URL and parse the RDFa
            opener = urllib2.build_opener()
            request = urllib2.Request(url)
            request.add_header('User-Agent',
                     'CC Metadata Scaper http://wiki.creativecommons.org/Metadata_Scraper')
            contents= opener.open(request).read()
            subjects.append(url)

            triples = parser.parse_string(contents, url, sink)

            # look for possible predicates to follow
            for s in triples.keys():
                for p in triples[s].keys():
                    if p in FOLLOW_PREDICATES:

                        # for each value of the predicate to follow
                        for o in triples[s][p]:

                            # follow if we haven't already looked here
                            if o not in subjects:
                                self._load_source(o, subjects, triples)

        except Exception, e:
	    triples = {'_exception': str(e)}

        return triples

        
    @LogResult(LOG)
    def _triples(self, url, action='triples'):

        # initialize the result
        result = dict(
            source = url,
            action = action,
            referer = web.ctx.environ.get('HTTP_REFERER', '-')
            )

        # parse the RDFa from the document
        triples = self._load_source(url)

        ns_cc = 'http://creativecommons.org/ns#'
        ns_wr = 'http://web.resource.org/cc/'

        # mash web.resource assertions to cc.org/ns
        for s in triples.keys():

            if s[:1] == '_': continue

            # walk each predicate, checking if it's in the web.resource ns
            for p in triples[s].keys():

                if p.find(ns_wr) == 0:
                    # map this back to cc.org/ns#
                    triples[s][ns_cc + p[len(ns_wr):]] = triples[s][p]
                    del triples[s][p]
                    
        # add the triples to the result
        result['triples'] = triples
        result['subjects'] = triples.keys()
        gc.collect()

        return result

class Triples(ScrapeRequestHandler):

    def GET(self):

        web.header("Content-Type","text/plain")
        print json.dumps(self._triples(web.input().get('url','')))

class Scrape(ScrapeRequestHandler):
    
    def GET(self):

        url = web.input().get('url', '')

        # parse the RDFa from the document
        triples = self._triples(url, 'scrape')['triples']

        ns_cc = 'http://creativecommons.org/ns#'
        ns_xh = 'http://www.w3.org/1999/xhtml/vocab#'
        ns_dc = 'http://purl.org/dc/elements/1.1/'

        # extract the bits we care about
        license_url = triples.setdefault(url, {}).get(
            ns_xh+'license', triples[url].get(
            ns_cc+'license', ['']))[0]

        attr_name = triples.setdefault(url, {}).get(
            ns_cc+'attributionName', [''])[0]

        attr_url = triples.setdefault(url, {}).get(
            ns_cc+'attributionURL', [''])[0]

        more_perms = triples.setdefault(url, {}).get(
            ns_cc+'morePermissions', [''])[0]
        more_perms_domain = urlparse.urlparse(more_perms)[1]

        # allow ads with non-commercial use?
        if ("http://creativecommons.org/ns#Advertising" in 
            triples.setdefault(url, {}).get(ns_cc + 'permission', [])):
           allow_ads = "Using this work on ad-supported sites is allowed."
        elif ("http://creativecommons.org/ns#Advertising" in 
            triples.setdefault(url, {}).get(ns_cc + 'prohibition', [])):
           allow_ads = "Using this work on ad-supported sites is prohibited."
        else:
           allow_ads = False

        # commerical rights / agent support
        commercial_license = triples.setdefault(url, {}).get(
            ns_cc+'commercialLicense', [''])[0]
        more_perms_agent = ''

        if commercial_license:
            # check for agent information
            dc_publisher = triples.setdefault(commercial_license, {}).get(
                ns_dc + 'publisher', [None])[0]

            if dc_publisher:
                more_perms_agent = triples.setdefault(dc_publisher, {}).get(
                    ns_dc + 'title', [''])[0]

        # assemble a dictionary to serialize
        attribution_info = {'_action':'scrape',
                            '_source':url,
                            'licenseUrl':license_url,
                            'attributionName':attr_name,
                            'attributionUrl':attr_url,
                            'morePermissions':more_perms,
                            'morePermissionsDomain':more_perms_domain,
                            'morePermissionsAgent':more_perms_agent,
                            'allowAdvertising':allow_ads,
                            'commercialLicense':commercial_license,
                            }

        # return the data encoded as JSON
        gc.collect()

        print json.dumps(attribution_info)


if __name__ == "__main__": 
    web.run(urls, globals())
