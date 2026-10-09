# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Replace stored routes (one per endpoint) w/ one anchor route per app.

    Service routes are now generated when the routing map is built.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    deleted = env["shopfloor.app"]._reset_endpoint_routes()
    _logger.info("Deleted %s shopfloor routes, registered anchor routes", deleted)
