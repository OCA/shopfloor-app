# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor Workstation Label Printer",
    "summary": "Adds a label printer configuration to shopfloor workstation.",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/shopfloor-app",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "depends": ["base_report_to_label_printer", "shopfloor_workstation"],
    "data": ["views/shopfloor_workstation.xml"],
    "installable": True,
}
