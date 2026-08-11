# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# # License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def partner(self):
        return self._simple_record()

    def partner_listing(self):
        schema = self._simple_record()
        schema.update(
            {"country": {"type": "string", "nullable": True, "required": False}}
        )
        return schema

    def country(self):
        return self._simple_record()
