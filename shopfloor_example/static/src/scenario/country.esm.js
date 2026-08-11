/**
 * Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */

import {ScenarioBaseMixin} from "/shopfloor_mobile_base/static/src/scenario/mixins.esm.js";
import {process_registry} from "/shopfloor_mobile_base/static/src/services/process_registry.esm.js";

const Country = {
    mixins: [ScenarioBaseMixin],
    template: `
        <Screen :screen_info="screen_info">
            <template v-slot:header>
                <state-display-info :info="state.display_info" v-if="state.display_info"/>
            </template>
            <div v-if="state_is('listing')">
                <manual-select
                    :records="state.data.records"
                    :key="make_state_component_key(['manual-select'])"
                    :options="{showActions: false}"
                    />
            </div>
            <div v-if="state_is('detail')">
                <detail-country_example :record="state.data.record" />
            </div>
            <div class="button-list button-vertical-list full">
                <v-row align="center" v-if="state_is('detail')">
                    <v-col class="text-center" cols="12">
                        <btn-action @click="state.on_jump_to_partners">View partners from this country</btn-action>
                    </v-col>
                </v-row>
                <v-row align="center">
                    <v-col class="text-center" cols="12">
                        <btn-back />
                    </v-col>
                </v-row>
            </div>
        </Screen>
        `,
    data: function () {
        return {
            usage: "country_example",
            initial_state_key: "listing",
            states: {
                listing: {
                    display_info: {
                        title: "Select country",
                    },
                    enter: () => {
                        this.wait_call(this.odoo.get("country_list"));
                    },
                    events: {
                        select: "on_select",
                    },
                    on_select: (selected) => {
                        if (selected)
                            this.wait_call(this.odoo.get(["detail", selected.id]));
                    },
                },
                detail: {
                    display_info: {
                        title: "Country detail",
                    },
                    on_jump_to_partners: () => {
                        this.wait_call(
                            this.odoo.post([
                                "detail",
                                this.state.data.record.id,
                                "jump_to_partners",
                            ])
                        );
                    },
                },
            },
        };
    },
};

process_registry.add("country_example", Country);

export default Country;
