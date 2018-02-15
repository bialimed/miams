#!/usr/bin/env python3

#
# Copyright (C) 2015 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import cherrypy
import cgi
import tempfile
import json
import sys
import datetime
from functools import wraps
import time
import os
import argparse

try:
    import _preamble
except ImportError:
    sys.exc_clear()

from jflow.server import JFlowServer


WEB_DIR = os.path.abspath(os.path.join(__file__, "../../docs"))

class AppServer( JFlowServer ):
    
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/app/index.html")


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", dest="daemon", default=False, help="Run the server as daemon")
    args = vars(parser.parse_args())

    app_conf = {
        '/': 
            {'tools.staticdir.root': WEB_DIR, 'tools.CORS.on': True},
        os.path.join('/', 'css'): 
            {'tools.staticdir.on'  : True, 'tools.staticdir.dir' : './css/'},
        os.path.join('/', 'js'): 
            {'tools.staticdir.on'  : True, 'tools.staticdir.dir' : './js/'},
        os.path.join('/', 'img'): 
            {'tools.staticdir.on'  : True, 'tools.staticdir.dir' : './img/'},
        os.path.join('/', 'fonts'): 
            {'tools.staticdir.on'  : True, 'tools.staticdir.dir' : './fonts/'},
        os.path.join('/', 'app'): 
            {'tools.staticdir.on'  : True, 'tools.staticdir.dir' : './'}
    }
    
    JFlowServer.quickstart(AppServer, app_conf, daemon=args["daemon"])
    
