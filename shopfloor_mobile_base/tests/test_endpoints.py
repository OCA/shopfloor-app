# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.addons.shopfloor_base.tests.common_http import HttpCommonCase


class TestEndpointsCase(HttpCommonCase):
    def test_call(self):
        route = self.shopfloor_app.url
        response = self._make_request(route)
        self.assertEqual(response.status_code, 200)

    def test_call_manifest(self):
        route = self.shopfloor_app.url + "manifest.json"
        response = self._make_request(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
