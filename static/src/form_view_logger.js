import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
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

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.viewHistoryOrm = useService("orm");

        useEffect(
            () => {
                const resModel = this.props.resModel;
                if (resModel) {
                    this.viewHistoryOrm.call("view.history", "log_list", [resModel]).catch(() => {});
                }
            },
            () => [this.props.resModel]
        );
    },
});
