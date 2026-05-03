import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useEffect } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);

        useEffect(
            () => {
                const root = this.model?.root;
                if (!root || root.isNew || !root.resId) {
                    return;
                }
                const resModel = this.props.resModel;
                if (!resModel) {
                    return;
                }
                const key = `${resModel}:${root.resId}`;
                if (this._viewHistoryLastKey === key) {
                    return;
                }
                this._viewHistoryLastKey = key;
                this.orm.call("view.history", "log_view", [resModel, root.resId]).catch(() => {});
            },
            () => [this.props.resModel, this.model?.root?.resId]
        );
    },
});
