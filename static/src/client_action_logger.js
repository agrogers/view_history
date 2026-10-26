import { registry } from "@web/core/registry";

registry.category("services").add("view_history.client_action_logger", {
    dependencies: ["action", "orm"],

    start(_env, { action, orm }) {
        const trackCurrentAction = (previousController) => {
            const controller = action.currentController;
            const clientAction = controller?.action;

            if (
                !controller ||
                controller === previousController ||
                !controller.Component ||
                clientAction?.type !== "ir.actions.client" ||
                clientAction.target === "new"
            ) {
                return;
            }

            let originalAction = {};
            try {
                originalAction = JSON.parse(clientAction._originalAction || "{}");
            } catch (error) {
                console.warn("View History: unable to read client action parameters", error);
            }
            const params = clientAction.id
                ? {}
                : originalAction.params || clientAction.params || {};
            const context = clientAction.id
                ? {}
                : originalAction.context || clientAction.context || {};

            orm.call("view.history", "log_client_action", [
                clientAction.tag,
                controller.displayName || clientAction.name || clientAction.tag,
                clientAction.id || false,
                params,
                context,
                clientAction.path || false,
                clientAction.target || false,
            ]).catch((error) => {
                console.warn("View History: failed to log client action", error);
            });
        };

        for (const methodName of ["doAction", "loadState", "restore"]) {
            const method = action[methodName].bind(action);
            action[methodName] = async (...args) => {
                const previousController = action.currentController;
                const result = await method(...args);
                trackCurrentAction(previousController);
                return result;
            };
        }
    },
});
