/**
 * Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {process_registry} from "/shopfloor_mobile_base/static/src/services/process_registry.esm.js";
import {translation_registry} from "/shopfloor_mobile_base/static/src/services/translation_registry.esm.js";

// Clone the original component
const DemoCheckout = process_registry.extend("checkout", {
    // `extend` accepts a path to the final key
    "methods.screen_title": function () {
        return this.$t("shopfloor_demo.checkout.title");
    },
});

// Replace process component
process_registry.replace("checkout", DemoCheckout);

// Add new translations
translation_registry.add(
    "en-US.shopfloor_demo.checkout.title",
    "Demo alternative title"
);
translation_registry.add(
    "fr-FR.shopfloor_demo.checkout.title",
    "Titre alternatif de la démo"
);
translation_registry.add(
    "de-DE.shopfloor_demo.checkout.title",
    "Demo alternativer Titel"
);
