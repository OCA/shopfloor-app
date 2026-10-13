# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.tests import Form

from odoo.addons.shopfloor_base.utils import APP_VERSION

from .common import CommonCase


# @tagged("-at_install")
class TestShopfloorApp(CommonCase):
    @classmethod
    def setUpClassUsers(cls):  # pylint: disable=missing-return
        super().setUpClassUsers()
        cls.env = cls.env(user=cls.shopfloor_manager)
        return

    @classmethod
    def setUpClassBaseData(cls):  # pylint: disable=missing-return
        super().setUpClassBaseData()
        cls.records = cls.env["shopfloor.app"].create(
            {
                "name": "A wonderful test app",
                "tech_name": "test_app",
                "short_name": "Test app",
            }
        ) + cls.env["shopfloor.app"].create(
            {
                "name": "A wonderful test app 2",
                "tech_name": "test_app_2",
                "short_name": "Test app 2",
            }
        )
        return

    def test_app_create(self):
        # fmt: off
        expected = [
            {
                "api_route": "/shopfloor/api/test_app",
                "url": "/shopfloor/app/test_app/",
            },
            {
                "api_route": "/shopfloor/api/test_app_2",
                "url": "/shopfloor/app/test_app_2/",
            },
        ]
        # fmt: on
        self.assertRecordValues(self.records, expected)

    def _test_registered_routes(self, rec):
        rec._register_controllers(init=True)
        # Only one anchor rule is stored per app
        rules = list(rec._registered_routes())
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertEqual(rule.key, f"shopfloor.app:{rec.id}")
        self.assertEqual(rule.route, rec.api_route)
        self.assertEqual(rule.route_group, rec._route_group())
        self.assertTrue(rule.endpoint_hash)
        self.assertEqual(
            rule.options["generator"],
            {
                "model": "shopfloor.app",
                "res_id": rec.id,
                "method_name": "_generate_routes",
            },
        )
        # Service routes are generated
        _check = {}
        for url, endpoint in rule.iter_routing_rules(self.env):
            self.assertEqual(endpoint.routing["type"], "restapi")
            self.assertEqual(endpoint.routing["auth"], rec.auth_type)
            self.assertEqual(endpoint.routing["routes"], [url])
            self.assertEqual(endpoint.func.__name__, "_process_endpoint")
            service, method_name = url.split("/")[-2:]
            self.assertEqual(endpoint.args, (rec.id, service, method_name))
            _check[url] = set(endpoint.routing["methods"])
        expected = {
            f"/shopfloor/api/{rec.tech_name}/app/user_config": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/user/menu": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/user/user_info": {"POST"},
            f"/shopfloor/api/{rec.tech_name}/menu/search": {"GET"},
            f"/shopfloor/api/{rec.tech_name}/profile/search": {"GET"},
            f"/shopfloor/api/{rec.tech_name}/scan_anything/scan": {"POST"},
        }
        for route, method in expected.items():
            self.assertEqual(
                _check[route], method, f"{route}: {method} != {_check[route]}"
            )

        expected = sorted([f"{k} ({', '.join(v)})" for k, v in expected.items()])
        rec.invalidate_recordset(["registered_routes"])
        self.assertEqual(
            sorted(rec.registered_routes.splitlines()),
            expected,
            f"{rec.tech_name} failed",
        )

    def test_registered_routes(self):
        rec1, rec2 = self.records
        self._test_registered_routes(rec1)
        self._test_registered_routes(rec2)

    def test_reset_endpoint_routes(self):
        registry = self.records._endpoint_registry
        handler = {
            "klass_dotted_path": (
                "odoo.addons.shopfloor_base.controllers.main.ShopfloorController"
            ),
            "method_name": "_process_endpoint",
        }
        other_handler = {
            "klass_dotted_path": (
                "odoo.addons.endpoint_route_handler.controllers.main."
                "EndpointNotFoundController"
            ),
            "method_name": "auto_not_found",
        }

        def _rule(key, group, opts_handler):
            route = f"/test_reset/{key}"
            return registry.make_rule(
                key,
                route,
                {"handler": opts_handler},
                {"routes": [route], "methods": ["POST"]},
                f"hash-{key}",
                route_group=group,
            )

        registry.update_rules(
            [
                # legacy route of an existing app
                _rule("legacy", self.records[0]._route_group(), handler),
                # route of an app deleted or renamed
                _rule("orphan", "shopfloor.app:gone", handler),
                # shopfloor handler in another group
                _rule("other_group", "something", handler),
                # not related to shopfloor
                _rule("unrelated", "something", other_handler),
            ]
        )
        self.records[1].sudo().active = False
        self.env["shopfloor.app"].sudo()._reset_endpoint_routes()
        keys = {
            r.key for r in registry.get_rules(keys=("legacy", "orphan", "other_group"))
        }
        self.assertFalse(keys)
        self.assertTrue(list(registry.get_rules(keys=("unrelated",))))
        # One anchor per active app
        anchors = list(self.records[0]._registered_routes())
        self.assertEqual(
            [r.key for r in anchors], [f"shopfloor.app:{self.records[0].id}"]
        )
        self.assertFalse(list(self.records[1]._registered_routes()))

    def test_unregister_legacy_rules(self):
        rec = self.records[0]
        rec._register_controllers(init=True)
        # Simulate a legacy rule (one per endpoint) left in the table
        registry = rec._endpoint_registry
        legacy = registry.make_rule(
            "legacy",
            f"{rec.api_route}/app/user_config",
            {
                "handler": {
                    "klass_dotted_path": (
                        "odoo.addons.shopfloor_base.controllers.main."
                        "ShopfloorController"
                    ),
                    "method_name": "_process_endpoint",
                }
            },
            {"routes": [f"{rec.api_route}/app/user_config"], "methods": ["POST"]},
            "legacy-hash",
            route_group=rec._route_group(),
        )
        registry.update_rules([legacy])
        self.assertEqual(len(list(rec._registered_routes())), 2)
        rec._unregister_controllers()
        self.assertFalse(list(rec._registered_routes()))

    def test_api_url_for_service(self):
        app = self.shopfloor_app
        self.assertEqual(
            app.api_url_for_service("profile"),
            f"/shopfloor/api/{app.tech_name}/profile",
        )
        self.assertEqual(
            app.api_url_for_service("profile", "search"),
            f"/shopfloor/api/{app.tech_name}/profile/search",
        )
        self.assertEqual(
            app.api_url_for_service("app", "user_config"),
            f"/shopfloor/api/{app.tech_name}/app/user_config",
        )

    def test_make_app_info(self):
        info = self.shopfloor_app._make_app_info()
        expected = {
            "auth_type": "user_endpoint",
            "base_url": "/shopfloor/api/test/",
            "url": "/shopfloor/app/test/",
            "demo_mode": False,
            "manifest_url": "/shopfloor/app/test/manifest.json",
            "name": "Test",
            "profile_required": False,
            "running_env": "prod",
            "short_name": "test",
            "version": APP_VERSION,
            "lang": {
                "default": False,
                "enabled": [],
            },
        }
        self.assertEqual(info, expected)
        info = self.shopfloor_app._make_app_info(demo=True)
        self.assertEqual(info["demo_mode"], True)
        lang_en, lang_fr = self.env.ref("base.lang_en"), self.env.ref("base.lang_fr")
        lang_fr.sudo().active = True
        self.shopfloor_app.sudo().lang_id = lang_en
        self.shopfloor_app.sudo().lang_ids = lang_en + lang_fr
        info = self.shopfloor_app._make_app_info()
        self.assertEqual(
            info["lang"], {"default": "en-US", "enabled": ["en-US", "fr-FR"]}
        )

    def test_make_app_manifest(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "web.base.url", "http://foo.com"
        )
        param = "http://foo.com"
        manifest = self.shopfloor_app._make_app_manifest()
        expected = {
            "name": self.shopfloor_app.name,
            "short_name": self.shopfloor_app.short_name,
            "start_url": param + self.shopfloor_app.url,
            "scope": param + self.shopfloor_app.url,
            "id": self.shopfloor_app.url,
            "display": "fullscreen",
            "icons": [],
        }
        self.assertEqual(manifest, expected)

    def test_lang_onchanges(self):
        lang_en, lang_fr = self.env.ref("base.lang_en"), self.env.ref("base.lang_fr")
        lang_fr.sudo().active = True
        form = Form(self.shopfloor_app.with_user(self.shopfloor_manager))
        # No avail langs
        self.assertFalse(form.lang_id)
        self.assertFalse(form.lang_ids)
        form.lang_id = lang_en
        # Avail langs updated
        self.assertIn(lang_en, form.lang_ids)
        # Replace avail w/ FR
        form.lang_ids.add(lang_fr)
        form.lang_ids.remove(lang_en.id)
        # lang wiped out
        self.assertFalse(form.lang_id)
