import { patch } from "@web/core/utils/patch";
import { View } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { useEffect } from "@odoo/owl";

patch(View.prototype, {
    async loadView(props) {
        await super.loadView(...arguments);
        if (props.type !== "form" && props.type !== "list") {
            return;
        }
        const Controller = this.Controller;
        const { resModel, type } = props;
        this.Controller = class extends Controller {
            setup() {
                super.setup?.(...arguments);
                const orm = useService("orm");

                useEffect(
                    () => {
                        if (type === "list") {
                            if (resModel) {
                                orm.call("view.history", "log_list", [resModel]).catch(() => {});
                            }
                            return;
                        }
                        const root = this.model?.root;
                        if (!root || root.isNew || !root.resId || !resModel) {
                            return;
                        }
                        const key = `${resModel}:${root.resId}`;
                        if (this._viewHistoryLastKey === key) {
                            return;
                        }
                        this._viewHistoryLastKey = key;
                        orm.call("view.history", "log_view", [resModel, root.resId]).catch(() => {});
                    },
                    () =>
                        type === "list"
                            ? [resModel]
                            : [resModel, this.model?.root?.resId]
                );
            }
        };
    },
});
