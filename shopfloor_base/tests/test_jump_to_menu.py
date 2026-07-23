# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import json

import cerberus

from odoo.addons.component.core import Component

from .common import CommonCase


class TestValidatorResponseJumpToMenu(CommonCase):
    """`jump_to_menu` must be usable as a next_state on every scenario
    without any scenario having to declare it in its own `_states()`.
    """

    def _get_validator(self, states):
        # Each test method gets its own usage: components are registered
        # under `MetaComponent`'s global registry by `_name`, which persists
        # across test methods in this class. Reusing the same `_name`/`_usage`
        # would merge every test's `_states()` into one another instead of
        # keeping them isolated.
        usage = f"test.jump_to_menu.{self._testMethodName}.validator.response"

        class _TestValidatorResponse(Component):
            _name = f"shopfloor.{usage}"
            _inherit = "base.shopfloor.validator.response"
            _usage = usage

            def _states(self):
                return states

        with self.work_on_services() as work:
            _TestValidatorResponse._build_component(work.components_registry)
            return work.component(usage=usage)

    def test_jump_to_menu_added_automatically(self):
        validator = self._get_validator({"start": {}, "foo": {}})
        schema = validator._response_schema(next_states=["foo"])
        self.assertEqual(
            schema["data"]["schema"]["jump_to_menu"],
            {"type": "dict", "schema": validator._jump_to_menu_schema()},
        )

    def test_jump_to_menu_not_added_without_next_states(self):
        validator = self._get_validator({"start": {}})
        schema = validator._response_schema()
        self.assertNotIn("jump_to_menu", schema["data"]["schema"])

    def test_jump_to_menu_schema_can_be_overridden_in_states(self):
        custom_schema = {"custom": {"type": "string"}}
        validator = self._get_validator({"start": {}, "jump_to_menu": custom_schema})
        schema = validator._response_schema(next_states=["jump_to_menu"])
        self.assertEqual(
            schema["data"]["schema"]["jump_to_menu"],
            {"type": "dict", "schema": custom_schema},
        )

    def test_states_data_is_coerced_to_json(self):
        # states_data: a {state_key: data} map for the states of the target
        # scenario that need seeding, because a scenario's state can need
        # data computed/stored on a different state; the landing state
        # (next_state) is included too if it needs data.
        validator = self._get_validator({"start": {}})
        schema = validator._jump_to_menu_schema()
        cerberus_validator = cerberus.Validator(schema)
        # A dict is transparently dumped to a JSON string.
        self.assertTrue(
            cerberus_validator.validate(
                {
                    "menu_id": 1,
                    "next_state": "select_line",
                    "states_data": {
                        "scan_location": {"buffer": {}},
                        "select_picking_type": {"picking_type": {}},
                        "select_line": {"move_line": {}},
                    },
                }
            ),
            cerberus_validator.errors,
        )
        self.assertEqual(
            cerberus_validator.document["states_data"],
            json.dumps(
                {
                    "scan_location": {"buffer": {}},
                    "select_picking_type": {"picking_type": {}},
                    "select_line": {"move_line": {}},
                }
            ),
        )
        # An already JSON-encoded string is left untouched.
        self.assertTrue(
            cerberus_validator.validate(
                {
                    "menu_id": 1,
                    "next_state": "listing",
                    "states_data": json.dumps({"listing": {"records": []}}),
                }
            ),
            cerberus_validator.errors,
        )
        # The field is optional.
        self.assertTrue(
            cerberus_validator.validate({"menu_id": 1, "next_state": "listing"}),
            cerberus_validator.errors,
        )

    def test_states_data_rejects_invalid_json(self):
        validator = self._get_validator({"start": {}})
        schema = validator._jump_to_menu_schema()
        cerberus_validator = cerberus.Validator(schema)
        self.assertFalse(
            cerberus_validator.validate(
                {
                    "menu_id": 1,
                    "next_state": "listing",
                    "states_data": "not valid json",
                }
            )
        )
        self.assertIn("states_data", cerberus_validator.errors)
