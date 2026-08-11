# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json

from odoo.addons.shopfloor_base.tests.common import CommonCase


class TestCountryServiceCase(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):  # pylint: disable=missing-return
        super().setUpClassBaseData()
        cls.record = cls.env.ref("base.be")
        cls.partner = cls.env.ref("base.res_partner_4")
        cls.partner.sudo().country_id = cls.record

    def _get_service(self):
        with self.work_on_services() as work:
            return work.component(usage="country_example")

    def test_country_data(self):
        self.assertEqual(
            self.data.country(self.record),
            {"id": self.record.id, "name": self.record.name},
        )

    def test_country_data_detail(self):
        self.assertEqual(
            self.data_detail.country_detail(self.record),
            {
                "id": self.record.id,
                "name": self.record.name,
                "code": self.record.code,
                "phone_code": self.record.phone_code,
            },
        )

    def test_detail(self):
        service = self._get_service()
        res = service.dispatch("detail", params={"country_id": self.record.id})
        self.assertEqual(
            res,
            {
                "data": {
                    "detail": {"record": self.data_detail.country_detail(self.record)}
                },
                "next_state": "detail",
            },
        )

    def test_listing(self):
        service = self._get_service()
        all_records = self.env["res.country"].search([])
        res = service.dispatch("country_list")
        self.assertEqual(
            res,
            {
                "data": {"listing": {"records": self.data.countries(all_records)}},
                "next_state": "listing",
            },
        )

    def test_jump_to_partners(self):
        service = self._get_service()
        res = service.dispatch(
            "jump_to_partners", params={"country_id": self.record.id}
        )
        menu = self.env.ref("shopfloor_example.shopfloor_menu_partners_demo")
        partners = self.env["res.partner"].search([("country_id", "=", self.record.id)])
        self.assertEqual(
            res,
            {
                "data": {
                    "jump_to_menu": {
                        "menu_id": menu.id,
                        "next_state": "listing",
                        "states_data": json.dumps(
                            {
                                "listing": {
                                    "records": self.data.partner_listing(partners)
                                }
                            }
                        ),
                    }
                },
                "next_state": "jump_to_menu",
            },
        )
