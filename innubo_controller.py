# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011-TODAY MINORISA (http://www.minorisa.net)
#                             All Rights Reserved.
#                             Minorisa <contact@minorisa.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import http
from openerp.http import request
import os
import datetime
import mimetypes

# BUNDLE_MAXAGE = 60 * 60 * 24 * 7
BUNDLE_MAXAGE = 10


def make_conditional(response, last_modified=None, etag=None, max_age=0):
    """ Makes the provided response conditional based upon the request,
    and mandates revalidation from clients

    Uses Werkzeug's own :meth:`ETagResponseMixin.make_conditional`, after
    setting ``last_modified`` and ``etag`` correctly on the response object

    :param response: Werkzeug response
    :type response: werkzeug.wrappers.Response
    :param datetime.datetime last_modified: last modification date of the response content
    :param str etag: some sort of checksum of the content (deep etag)
    :return: the response object provided
    :rtype: werkzeug.wrappers.Response
    """
    response.cache_control.must_revalidate = True
    response.cache_control.max_age = max_age
    if last_modified:
        response.last_modified = last_modified
    if etag:
        response.set_etag(etag)
    return response.make_conditional(request.httprequest)


class DocHelp(http.Controller):

    @http.route([
        '/dochelp',
        '/dochelp/<path:xpath>'], type='http', auth='none')
    def dochelp(self, xpath=None, **kw):
        s = os.path.dirname(__file__)
        if xpath is None:
            xpath = 'index.html'
        ss = os.path.join(s, 'build', 'html', xpath)
        f = open(ss)
        t = os.path.getmtime(ss)
        last_modified = datetime.datetime.fromtimestamp(t)
        mimetype = mimetypes.guess_type(xpath)[0]
        ret = f.read()
        response = request.make_response(ret, [('Content-Type', mimetype)])
        return make_conditional(response, last_modified, max_age=BUNDLE_MAXAGE)
