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
        // Use the action_id / action_path supplied by the server (from ir.actions.act_window
        // rows that have a path set) so the correct app menu is highlighted regardless of
        // which app the user is currently in when they click a history entry.
        const action = {
            type: "ir.actions.act_window",
            res_model: item.model,
            res_id: item.res_id,
            views: [[false, "form"]],
            target: "current",
        };
        if (item.action_id) {
            action.id = item.action_id;
        }
        if (item.action_path) {
            action.path = item.action_path;
        }
        // Always navigate to the record's own app context, not stacked on top of
        // whatever app the user is currently in.  Without clearBreadcrumbs the
        // parent action ("contacts", etc.) stays in the action stack and its path
        // ends up prepended to the URL, causing the wrong menu to highlight.
        this.action.doAction(action, { clearBreadcrumbs: true });
    }
}

registry.category("systray").add("view_history.systray", { Component: ViewHistorySystray }, { sequence: 50 });
