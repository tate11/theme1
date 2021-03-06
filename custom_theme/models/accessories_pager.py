# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo import tools
from odoo.tools import ustr
from odoo.http import request
from odoo.tools.translate import _
import math
import werkzeug
from werkzeug.exceptions import NotFound

class Accessories_custom(models.Model):

    _name = "accessories"

    @api.model
    def pager(self, url, total, page=1, step=30, scope=5, url_args=None):
        """ Generate a dict with required value to render `website.pager` template. This method compute
            url, page range to display, ... in the pager.
            :param url : base url of the page link
            :param total : number total of item to be splitted into pages
            :param page : current page
            :param step : item per page
            :param scope : number of page to display on pager
            :param url_args : additionnal parameters to add as query params to page url
            :type url_args : dict
            :returns dict
        """
        # Compute Pager
        page_count = int(math.ceil(float(total) / step))

        page = max(1, min(int(page if str(page).isdigit() else 1), page_count))
        scope -= 1

        pmin = max(page - int(math.floor(scope/2)), 1)
        pmax = min(pmin + scope, page_count)

        if pmax - pmin < scope:
            pmin = pmax - scope if pmax - scope > 0 else 1

        def get_url(page):
            _url = "%s/page/%s" % (url, page) if page > 1 else url
            if url_args:
                _url = "%s?%s" % (_url, werkzeug.url_encode(url_args))
            return _url

        return {
            "page_count": page_count,
            "offset": (page - 1) * step,
            "page": {
                'url': get_url(page),
                'num': page
            },
            "page_start": {
                'url': get_url(pmin),
                'num': pmin
            },
            "page_previous": {
                'url': get_url(max(pmin, page - 1)),
                'num': max(pmin, page - 1)
            },
            "page_next": {
                'url': get_url(min(pmax, page + 1)),
                'num': min(pmax, page + 1)
            },
            "page_end": {
                'url': get_url(pmax),
                'num': pmax
            },
            "pages": [
                {'url': get_url(page), 'num': page} for page in xrange(pmin, pmax+1)
            ]
        }
