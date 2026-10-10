# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import hashlib
import json
import logging

from odoo import api, fields, models, tools
from odoo.tools import DotDict

from odoo.addons.base_rest.tools import ROUTING_DECORATOR_ATTR, _inspect_methods
from odoo.addons.component.core import _component_databases
from odoo.addons.endpoint_route_handler.utils import make_endpoint

from ..controllers.main import ShopfloorController
from ..utils import APP_VERSION, RUNNING_ENV

_logger = logging.getLogger(__file__)


class ShopfloorApp(models.Model):
    """Backend for a Shopfloor app."""

    _name = "shopfloor.app"
    _inherit = ["collection.base", "endpoint.route.sync.mixin"]
    _description = "A Shopfloor application"

    name = fields.Char(required=True, translate=True)
    short_name = fields.Char(
        required=True, translate=True, help="Needed for app manifest"
    )
    # Unique name
    tech_name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)
    category = fields.Selection(selection=[("", "None")])
    api_route = fields.Char(
        compute="_compute_api_route",
        compute_sudo=True,
        help="Base route for endpoints attached to this app, public version.",
    )
    api_route = fields.Char(
        compute="_compute_api_route",
        compute_sudo=True,
        help="""
        Base route for endpoints attached to this app,
        internal controller-ready version.
        """,
    )
    url = fields.Char(compute="_compute_url", help="Public URL to use the app.")
    api_docs_url = fields.Char(compute="_compute_url", help="Public URL for api docs.")
    auth_type = fields.Selection(
        selection="_selection_auth_type", default="user_endpoint"
    )
    registered_routes = fields.Text(
        compute="_compute_registered_routes",
        compute_sudo=True,
        help="Technical field to allow developers "
        "to check registered routes on the form",
        groups="base.group_no_one",
    )
    profile_ids = fields.Many2many(
        comodel_name="shopfloor.profile",
        string="Profiles",
        help="Profiles used by this app. "
        "This will determine menu items too."
        "However this field is not required "
        "in case you don't need profiles and menu items from the backend.",
    )
    profile_required = fields.Boolean(compute="_compute_profile_required", store=True)
    app_version = fields.Char(compute="_compute_app_version")
    lang_id = fields.Many2one(
        "res.lang",
        string="Default language",
        help="If set, the app will be first loaded with this lang.",
    )
    lang_ids = fields.Many2many("res.lang", string="Available languages")

    _sql_constraints = [("tech_name", "unique(tech_name)", "tech_name must be unique")]

    _api_route_path = "/shopfloor/api/"

    @api.depends("tech_name")
    def _compute_api_route(self):
        for rec in self:
            rec.api_route = rec._api_route_path + rec.tech_name

    _base_url_path = "/shopfloor/app/"
    _base_api_docs_url_path = "/shopfloor/api-docs/"

    @api.depends("tech_name")
    def _compute_url(self):
        for rec in self:
            full_url = rec._base_url_path + rec.tech_name
            rec.url = full_url.rstrip("/") + "/"
            rec.api_docs_url = rec._base_api_docs_url_path + rec.tech_name

    @api.depends("tech_name")
    def _compute_registered_routes(self):
        for rec in self:
            vals = [
                f"{url} ({', '.join(endpoint.routing['methods'])})"
                for url, endpoint in rec._generate_routes()
            ]
            rec.registered_routes = "\n".join(sorted(vals))

    @api.depends("profile_ids")
    def _compute_profile_required(self):
        for rec in self:
            rec.profile_required = bool(rec.profile_ids)

    def _compute_app_version(self):
        # Override this to choose your own versioning policy
        for rec in self:
            rec.app_version = APP_VERSION

    def _selection_auth_type(self):
        return self.env["endpoint.route.handler"]._selection_auth_type()

    def api_url_for_service(self, service_name, endpoint=None):
        """Handy method to generate services' API URLs for current app."""
        return f"{self.api_route}/{service_name}/{endpoint or ''}".rstrip("/")

    def action_open_app(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.url,
            "target": "new",
        }

    def action_open_app_docs(self):
        return {
            "type": "ir.actions.act_url",
            "name": self.name,
            "url": self.api_docs_url,
            "target": "new",
        }

    def action_view_menu_items(self):
        xid = "shopfloor_base.action_shopfloor_menu"
        action = self.env["ir.actions.act_window"]._for_xml_id(xid)
        action["domain"] = [
            "|",
            ("id", "in", self.profile_ids.menu_ids.ids),
            ("profile_id", "=", False),
        ]
        return action

    def _routing_impacting_fields(self):
        return ("tech_name", "auth_type")

    def _prepare_endpoint_rules(self, options=None):
        """Register one anchor rule per app (`endpoint.route.sync.mixin` api).

        Routes of the services are not stored:
        they are generated when the routing map is built (see `_generate_routes`),
        hence new endpoints do not require any update of the `endpoint_route` table.
        """
        return [rec._make_anchor_rule() for rec in self]

    def _registered_endpoint_rule_keys(self):
        """Keys of all the rules of the app (`endpoint.route.sync.mixin` api).

        Includes legacy rules (one per endpoint) to clean them up.
        """
        return [x.key for x in self._registered_routes()]

    @api.model
    def _reset_endpoint_routes(self):
        """Drop all the shopfloor routes stored and register the anchor routes.

        Catch all the routes related to shopfloor, including legacy ones
        (one per endpoint) and the ones of apps deleted or renamed:
        any route of a `shopfloor.app:*` group or handled by `ShopfloorController`.
        Then register one anchor route per active app.

        :return: number of deleted routes
        """
        self.env.cr.execute(
            "DELETE FROM endpoint_route WHERE route_group LIKE %s OR opts LIKE %s",
            (f"{self._name}:%", "%ShopfloorController%"),
        )
        deleted = self.env.cr.rowcount
        self.search([])._register_controllers(clear_cache=False)
        self.env.registry.clear_cache("routing")
        return deleted

    def _anchor_rule_key(self):
        """Unique key of the anchor rule of the app."""
        return f"{self._name}:{self.id}"

    def _anchor_rule_options(self):
        """Delegate the routes of the app to `_generate_routes`."""
        return {
            "generator": {
                "model": self._name,
                "res_id": self.id,
                "method_name": "_generate_routes",
            }
        }

    def _base_routing(self):
        """Routing shared by all the endpoints of the app."""
        return {
            # SF endpoints use the `restapi` dispatcher provided by base_rest
            "type": "restapi",
            "auth": self.auth_type,
            "csrf": False,
            "readonly": False,
        }

    def _make_anchor_rule(self):
        """Build the anchor rule: the only row stored for the app."""
        options = self._anchor_rule_options()
        routing = dict(self._base_routing(), routes=[self.api_route], methods=None)
        # The hash identifies the rule:
        # it changes when routing data change, to refresh the routing map.
        endpoint_hash = hashlib.md5(
            json.dumps([self.api_route, options, routing], sort_keys=True).encode(),
            usedforsecurity=False,
        ).hexdigest()
        return self._endpoint_registry.make_rule(
            self._anchor_rule_key(),
            self.api_route,
            options,
            routing,
            endpoint_hash,
            route_group=self._route_group(),
        )

    def _generate_routes(self, rule=None):
        """Yield `(url, endpoint)` for all the endpoints of the app's services.

        Called by `endpoint_route_handler` when the routing map is built.
        """
        self.ensure_one()
        if not self._is_component_registry_ready():
            # Routes would be missing until the routing map is rebuilt.
            _logger.error(
                "Component registry not ready: routes of %s not generated",
                self.tech_name,
            )
            return
        for service in self._get_services():
            yield from self._generate_service_routes(service)

    def _register_hook(self):
        super()._register_hook()
        if not tools.sql.column_exists(self.env.cr, self._table, "registry_sync"):
            # `registry_sync` has been introduced recently.
            # If an env is loaded before the column gets created this can be broken.
            return True
        self._boot_base_rest_endpoints()

    def _boot_base_rest_endpoints(self):
        """Satisfy `base_rest` requirements for REST requests.

        1. register root paths
        2. decorate non decorated endpoints

        Note that at runtime this is done by
        `_register_controllers` and `_prepare_endpoint_rules`.

        TODO: trash for v16 if using `fastapi`.
        """
        domain = [("active", "=", True), ("registry_sync", "=", True)]
        self.search(domain)._register_base_rest_routes()
        services = self._get_services()
        for service in services:
            self._prepare_non_decorated_endpoints(service)

    def _register_controllers(self, init=False, options=None, clear_cache=True):
        super()._register_controllers(
            init=init, options=options, clear_cache=clear_cache
        )
        if not self:
            return
        self._register_base_rest_routes()

    def _register_base_rest_routes(self):
        # base_rest patches odoo http request to handle json request
        # using a special registry for rest routes
        for rec in self:
            self.env["rest.service.registration"]._register_rest_route(rec.api_route)

    def _registered_routes(self):
        registry = self.env["endpoint.route.handler"]._endpoint_registry
        return registry.get_rules_by_group(self._route_group())

    @api.model
    def _prepare_non_decorated_endpoints(self, service):
        # Autogenerate routing info where missing
        self.env["rest.service.registration"]._prepare_non_decorated_endpoints(service)

    def _generate_service_routes(self, service):
        """Yield `(url, endpoint)` for the decorated methods of the service."""
        self._prepare_non_decorated_endpoints(service)
        root_path = self.api_route.rstrip("/") + "/" + service._usage
        controller = ShopfloorController()
        for name, method in _inspect_methods(service.__class__):
            routing = getattr(method, ROUTING_DECORATOR_ATTR, None)
            if routing is None:
                continue
            for paths, http_method in routing["routes"]:
                # Only the 1st path is routed (as it has always been).
                url = root_path + "/" + paths[0].lstrip("/")
                endpoint = make_endpoint(
                    controller._process_endpoint,
                    self._service_endpoint_routing(url, http_method, routing),
                    pargs=(self.id, service._usage, name),
                )
                yield url, endpoint

    def _service_endpoint_routing(self, url, http_method, method_routing):
        """Routing of one endpoint: app defaults + method overrides."""
        routing = dict(self._base_routing(), routes=[url], methods=[http_method])
        for attr in ("auth", "cors", "csrf", "save_session"):
            if attr in method_routing:
                routing[attr] = method_routing[attr]
        return routing

    def _route_group(self):
        return f"{self._name}:{self.tech_name}"

    def _is_component_registry_ready(self):
        comp_registry = _component_databases.get(self.env.cr.dbname)
        return comp_registry and comp_registry.ready

    def _get_services(self):
        forced_services = self.env.context.get("sf_service_components")
        if forced_services:
            _logger.debug(
                "_get_services forced services: %s",
                ", ".join([x._usage for x in forced_services]),
            )
            return forced_services
        if not self._is_component_registry_ready():
            # No service is available before the registry has been loaded.
            # This is a very special case, when the odoo registry is being
            # built, it calls odoo.modules.loading.load_modules().
            return []
        return self.env["rest.service.registration"]._get_services(self._name)

    def _name_with_env(self):
        name = self.name
        if RUNNING_ENV and RUNNING_ENV != "prod":
            name += f" ({RUNNING_ENV})"
        return name

    def _make_app_info(self, demo=False):
        base_url = self.api_route.rstrip("/") + "/"
        return DotDict(
            name=self._name_with_env(),
            short_name=self.short_name,
            base_url=base_url,
            url=self.url,
            manifest_url=self.url + "manifest.json",
            auth_type=self.auth_type,
            profile_required=self.profile_required,
            demo_mode=demo,
            version=self.app_version,
            running_env=RUNNING_ENV,
            lang=self._app_info_lang(),
        )

    def _app_info_lang(self):
        enabled = []
        conv = self._app_convert_lang_code
        default = self.sudo().lang_id
        avail_langs = self.sudo().lang_ids
        if self.lang_ids:
            enabled = [conv(x.code) for x in avail_langs]
        return dict(
            default=conv(default.code) if default else False,
            enabled=enabled,
        )

    def _app_convert_lang_code(self, code):
        # TODO: we should probably let the front decide the format
        return code.replace("_", "-")

    def _make_app_manifest(self, icons=None, **kw):
        self = self.sudo()
        param = (
            self.env["ir.config_parameter"].get_param("web.base.url", "").rstrip("/")
        )
        manifest = {
            "name": self._name_with_env(),
            "short_name": self.short_name,
            "start_url": param + self.url,
            "scope": param + self.url,
            "id": self.url,
            "display": "fullscreen",
            "icons": icons or [],
        }
        manifest.update(kw)
        return manifest

    @api.onchange("lang_id")
    def _onchange_lang_id(self):
        if self.env.context.get("from_onchange__lang_ids"):
            return
        if self.lang_id and self.lang_id not in self.lang_ids:
            self.with_context(from_onchange__lang_id=1).lang_ids += self.lang_id

    @api.onchange("lang_ids")
    def _onchange_lang_ids(self):
        if self.env.context.get("from_onchange__lang_id"):
            return
        if self.lang_ids and self.lang_id and self.lang_id not in self.lang_ids:
            self.with_context(from_onchange__lang_ids=1).lang_id = False
