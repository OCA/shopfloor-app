/**
 * Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ItemDetailMixin} from "/shopfloor_mobile_base/static/src/components/detail/detail_mixin.esm.js";

Vue.component("detail-country_example", {
    mixins: [ItemDetailMixin],
    methods: {
        detail_fields() {
            return [
                {path: "code", label: "Code"},
                {path: "phone_code", label: "Phone code"},
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
