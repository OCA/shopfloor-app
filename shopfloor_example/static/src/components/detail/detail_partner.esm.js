/**
 * Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
 * @author Simone Orsi <simahawk@gmail.com>
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/src/components/detail/detail_mixin.esm.js";

Vue.component("detail-partner_example", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "ref", label: "Ref"},
                {
                    path: "email",
                    label: "Email",
                    // Not really needed... just an example
                    renderer: function (rec, field) {
                        return rec[field.path];
                    },
                },
            ];
        },
        card_options() {
            return {
                loud_labels: true,
                fields: this.detail_fields(),
            };
        },
    },
    template: `
    <div :class="$options._componentTag">

        <item-detail-card v-bind="$props" :options="card_options()" />

    </div>
`,
});
