# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component


class CountryExampleService(Component):
    """Country example.

    Small read-only scenario on a core model (`res.country`) requiring no
    extra dependency. Mainly used to demo `jump_to_menu`: from a country's
    detail screen you can jump straight into the `partner_example` scenario,
    pre-loaded with the partners of that country.
    """

    _inherit = "base.shopfloor.process"
    _name = "custom.example.country"
    _usage = "country_example"
    _description = __doc__

    @restapi.method(
        [(["/country_list"], "GET")],
        input_param=restapi.CerberusValidator("country_list"),
        output_param=restapi.CerberusValidator("country_list"),
    )
    def country_list(self, **params):
        """Return list of available countries."""
        domain = []
        if "name" in params:
            domain.append(("name", "like", params["name"]))
        records = self.env["res.country"].search(domain)
        return self._response_for_country_list(records)

    @restapi.method(
        [(["/detail/<int:country_id>"], "GET")],
        input_param=restapi.CerberusValidator("detail"),
        output_param=restapi.CerberusValidator("detail"),
    )
    def detail(self, country_id):
        """Retrieve full detail for country ID."""
        record = self.env["res.country"].browse(country_id).exists()
        if not record:
            message = self.msg_store.generic_record_not_found()
            records = self.env["res.country"].search([])
            return self._response_for_country_list(records, message=message)
        return self._response_for_detail(record)

    @restapi.method(
        [(["/detail/<int:country_id>/jump_to_partners"], "POST")],
        input_param=restapi.CerberusValidator("jump_to_partners"),
        output_param=restapi.CerberusValidator("jump_to_partners"),
    )
    def jump_to_partners(self, country_id):
        """Jump to the `partner_example` menu, pre-loaded with the partners
        of this country."""
        record = self.env["res.country"].browse(country_id).exists()
        if not record:
            message = self.msg_store.generic_record_not_found()
            records = self.env["res.country"].search([])
            return self._response_for_country_list(records, message=message)
        partners = self.env["res.partner"].search([("country_id", "=", record.id)])
        menu = self.env.ref("shopfloor_example.shopfloor_menu_partners_demo")
        jump_data = {
            "menu_id": menu.id,
            "next_state": "listing",
            "states_data": {
                "listing": {"records": self.data.partner_listing(partners)}
            },
        }
        return self._response(next_state="jump_to_menu", data=jump_data)

    def _response_for_detail(self, record, message=None, popup=None):
        data = {"record": self.data_detail.country_detail(record)}
        return self._response(
            next_state="detail", data=data, message=message, popup=popup
        )

    def _response_for_country_list(self, records, message=None, popup=None):
        data = {"records": self.data.countries(records)}
        return self._response(
            next_state="listing", data=data, message=message, popup=popup
        )


class ShopfloorCountryExampleValidator(Component):
    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.country_example.validator"
    _usage = "country_example.validator"

    def detail(self):
        return {
            "country_id": {"required": True, "type": "integer"},
        }

    def country_list(self):
        return {
            "name": {"required": False, "type": "string"},
        }

    def jump_to_partners(self):
        return {
            "country_id": {"required": True, "type": "integer"},
        }


class ShopfloorCountryExampleValidatorResponse(Component):
    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.country_example.validator.response"
    _usage = "country_example.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "detail": {
                "record": self.schemas._schema_dict_of(
                    self.schemas_detail.country_detail()
                )
            },
            "listing": {
                "records": self.schemas._schema_list_of(self.schemas.country()),
            },
        }

    def detail(self):
        return self._response_schema(next_states=["detail"])

    def country_list(self):
        return self._response_schema(next_states=["listing"])

    def jump_to_partners(self):
        return self._response_schema(next_states=["listing"])
