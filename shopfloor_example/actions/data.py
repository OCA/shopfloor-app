# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("res.partner")
    def partner(self, record, **kw):
        return self._jsonify(record, self._partner_parser, **kw)

    def partners(self, records, **kw):
        return self.partner(records, multi=True)

    @property
    def _partner_detail_parser(self):
        return self._simple_record()

    @ensure_model("res.partner")
    def partner_listing(self, records, **kw):
        return self._jsonify(records, self._partner_listing_parser, multi=True, **kw)

    @property
    def _partner_listing_parser(self):
        return ["id", "display_name:name", "country_id:country"]

    @ensure_model("res.country")
    def country(self, record, **kw):
        return self._jsonify(record, self._country_parser, **kw)

    def countries(self, records, **kw):
        return self.country(records, multi=True)

    @property
    def _country_parser(self):
        return ["id", "name"]
