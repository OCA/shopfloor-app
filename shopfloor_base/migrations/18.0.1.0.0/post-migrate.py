# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Force update endpoint_route table.

    Critical changes:

    * new `readonly` should be added to the stored route options
    * route type should be set to `restapi`
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env["shopfloor.app"]
    records = model.sudo().search([])
    for app in records:
        registry = app._endpoint_registry
        rules = list(registry.get_rules_by_group(app._route_group()))
        for rule in rules:
            rule.routing = dict(rule.routing, readonly=False, type="restapi")
        registry.update_rules(rules)
    _logger.info(
        "Forced endpoint route sync on %s records: %s", model._name, records.ids
    )
