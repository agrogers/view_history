from odoo import api, fields, models
from odoo.exceptions import AccessError


class ViewHistory(models.Model):
    _name = "view.history"
    _description = "View History"
    _order = "viewed_at desc, id desc"

    user_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="cascade",
        index=True,
        default=lambda self: self.env.user,
    )
    model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    viewed_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)

    @api.model
    def log_view(self, model, res_id):
        if not model or not res_id:
            return False
        if not self.env.user.log_view_history:
            return False
        target_model = self.env.get(model)
        if target_model is None:
            return False
        try:
            res_id = int(res_id)
        except (TypeError, ValueError):
            return False
        if res_id <= 0:
            return False
        if not target_model.sudo().browse(res_id).exists():
            return False
        self.sudo().create(
            {
                "user_id": self.env.user.id,
                "model": model,
                "res_id": res_id,
            }
        )
        return True

    @api.model
    def get_recent(self, limit=50):
        if not self.env.user.log_view_history:
            return []
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 15
        if limit <= 0:
            return []

        records = self.search(
            [("user_id", "=", self.env.user.id)],
            order="viewed_at desc, id desc",
            limit=limit, 
        )
        if not records:
            return []

        all_models = list(set(records.mapped("model")))
        model_names = {}
        model_modules = {}
        for item in self.env["ir.model"].search([("model", "in", all_models)]):
            model_names[item.model] = item.name
            if item.modules:
                model_modules[item.model] = item.modules.split(", ")[0]

        # Find the primary action (with a path set) for each model so the
        # history systray can navigate to the correct app context.
        model_actions = {}
        for action in self.env["ir.actions.act_window"].search(
            [("res_model", "in", all_models), ("path", "!=", False)],
            order="id asc",
        ):
            # Keep only the first match per model (lowest id = most fundamental action)
            if action.res_model not in model_actions:
                model_actions[action.res_model] = {
                    "action_id": action.id,
                    "action_path": action.path,
                }

        items = []
        for record in records:
            model = record.model
            res_id = record.res_id
            target_model = self.env.get(model)
            if target_model is None:
                continue
            try:
                target_model.check_access("read")
                target = target_model.browse(res_id)
                target.check_access("read")
            except AccessError:
                continue
            if not target.exists():
                continue
            icon_url = False
            for icon_field in ("type_icon", "icon", "image_1920"):
                if icon_field in target._fields and target[icon_field]:
                    icon_url = f"/web/image/{model}/{res_id}/{icon_field}"
                    break
            if not icon_url:
                module_name = model_modules.get(model)
                if module_name:
                    icon_url = f"/{module_name}/static/description/icon.png"
            display_name = target.display_name
            if model == "account.move" and hasattr(target, "partner_id") and target.partner_id:
                display_name = f"{display_name} - {target.partner_id.name}"
            item_data = {
                "id": record.id,
                "model": model,
                "model_name": model_names.get(model, model),
                "res_id": res_id,
                "display_name": display_name,
                "viewed_at": record.viewed_at,
                "icon_url": icon_url,
            }
            item_data.update(model_actions.get(model, {}))
            items.append(item_data)
        return items
