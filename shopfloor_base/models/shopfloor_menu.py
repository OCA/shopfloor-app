# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ShopfloorMenu(models.Model):
    _name = "shopfloor.menu"
    _description = "Menu displayed in the scanner application"
    _order = "sequence"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer()
    profile_id = fields.Many2one(
        "shopfloor.profile", string="Profile", help="Visible on this profile only"
    )
    scenario_id = fields.Many2one(
        comodel_name="shopfloor.scenario",
        required=True,
        ondelete="restrict",
        auto_join=True,
    )
    scenario_key = fields.Char(related="scenario_id.key")
    active = fields.Boolean(default=True)

    def _get_allowed_companies(self):
        """Return the companies the services of this menu should work with.

        Used to set `allowed_company_ids` in the env of the request.
        An empty recordset means no restriction.
        """
        return self.env["res.company"]
