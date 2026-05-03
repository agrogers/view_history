import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

import { Component, useState } from "@odoo/owl";

export class ViewHistorySystray extends Component {
    static template = "view_history.ViewHistorySystray";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: false,
            items: [],
        });
        this.labels = {
            empty: _t("No view history yet"),
            loading: _t("Loading..."),
            history: _t("View history"),
        };
    }

    async loadItems() {
        if (this.state.loading) {
            return;
        }
        this.state.loading = true;
        try {
            const items = await this.orm.call("view.history", "get_recent", [], { limit: 100 });
            this.state.items = Array.isArray(items) ? items : [];
        } finally {
            this.state.loading = false;
        }
    }

    onOpened() {
        this.loadItems();
    }

    openItem(item) {
        if (!item || !item.model || !item.res_id) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: item.model,
            res_id: item.res_id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("systray").add("view_history.systray", { Component: ViewHistorySystray }, { sequence: 50 });
