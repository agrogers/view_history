from odoo import api, fields, models
from odoo.exceptions import AccessError, MissingError
from odoo.fields import Binary, Image
from odoo.tools.image import image_data_uri


class IrModel(models.Model):
    _inherit = "ir.model"

    view_history_icon = fields.Image(
        string="View History Icon",
        max_width=128,
        max_height=128,
    )


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
    client_action_tag = fields.Char(index=True)
    client_action_name = fields.Char()
    client_action_params = fields.Json()
    client_action_context = fields.Json()
    client_action_path = fields.Char()
    client_action_target = fields.Char()

    @api.model
    def log_view(self, model, res_id):
        if not model or not res_id:
            return False
        if not self.env.user.log_view_history:
            return False
        target_model = self.env.get(model)
        if target_model is None or target_model._transient:
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
    def log_list(self, model):
        if not model or not self.env.user.log_view_history:
            return False
        target_model = self.env.get(model)
        if target_model is None or target_model._transient:
            return False
        try:
            target_model.check_access("read")
        except AccessError:
            return False
        self.sudo().create(
            {
                "user_id": self.env.user.id,
                "model": model,
                "res_id": 0,
            }
        )
        return True

    @api.model
    def log_client_action(
        self, tag, name=False, action_id=False, params=False, context=False, path=False, target=False
    ):
        if not tag or not self.env.user.log_view_history:
            return False
        if not isinstance(tag, str) or not tag.strip():
            return False

        try:
            action_id = int(action_id) if action_id else 0
        except (TypeError, ValueError):
            return False
        if action_id < 0:
            return False
        action_name = name if isinstance(name, str) else False
        action_params = params if isinstance(params, dict) else {}
        action_context = context if isinstance(context, dict) else {}
        action_path = path if isinstance(path, str) else False
        action_target = target if isinstance(target, str) else False
        if action_id:
            action = self.env["ir.actions.client"].browse(action_id).exists()
            if not action or action.tag != tag:
                return False
            try:
                action.check_access("read")
            except AccessError:
                return False
            action_name = action_name or action.display_name

        self.sudo().create(
            {
                "user_id": self.env.user.id,
                "model": "ir.actions.client",
                "res_id": action_id,
                "client_action_tag": tag,
                "client_action_name": action_name or tag,
                "client_action_params": action_params,
                "client_action_context": action_context,
                "client_action_path": action_path,
                "client_action_target": action_target,
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
        model_icons = {}
        for item in self.env["ir.model"].sudo().search([("model", "in", all_models)]):
            model_names[item.model] = item.name
            if item.modules:
                model_modules[item.model] = item.modules.split(", ")[0]
            if item.view_history_icon:
                model_icons[item.model] = image_data_uri(item.view_history_icon)

        # Find the primary action (with a path set) for each model so the
        # history systray can navigate to the correct app context.
        model_actions = {}
        for action in self.env["ir.actions.act_window"].sudo().search(
            [("res_model", "in", all_models), ("path", "!=", False)],
            order="id asc",
        ):
            # Keep only the first match per model (lowest id = most fundamental action)
            if action.res_model not in model_actions:
                model_actions[action.res_model] = {
                    "action_id": action.id,
                    "action_path": action.path,
                }

        client_action_ids = {
            record.res_id
            for record in records
            if record.client_action_tag and record.res_id
        }
        client_action_icons = {}
        if client_action_ids:
            action_refs = [
                f"ir.actions.client,{action_id}" for action_id in client_action_ids
            ]
            menus = self.env["ir.ui.menu"].with_context(
                {"ir.ui.menu.full_list": False}
            ).search([("action", "in", action_refs)])
            # Prefer the most specific visible menu when an action has multiple menu entries.
            for menu in menus.sorted(
                lambda item: (item.parent_path or "").count("/"),
                reverse=True,
            ):
                action = menu.action
                if (
                    action
                    and action._name == "ir.actions.client"
                    and action.id in client_action_ids
                    and menu.web_icon_data
                ):
                    client_action_icons.setdefault(
                        action.id,
                        image_data_uri(menu.web_icon_data),
                    )

        items = []
        seen = set()
        for record in records:
            model = record.model
            res_id = record.res_id
            key = (model, res_id, record.client_action_tag or False)
            if key in seen:
                continue
            seen.add(key)
            target_model = self.env.get(model)
            if target_model is None or target_model._transient:
                continue
            if record.client_action_tag:
                if res_id:
                    try:
                        target_model.check_access("read")
                        action = target_model.browse(res_id)
                        action.check_access("read")
                    except AccessError:
                        continue
                    if not action.exists() or action.tag != record.client_action_tag:
                        continue
                items.append(
                    {
                        "id": record.id,
                        "model": model,
                        "model_name": model_names.get(model, model),
                        "res_id": res_id,
                        "display_name": record.client_action_name or record.client_action_tag,
                        "viewed_at": record.viewed_at,
                        "icon_url": client_action_icons.get(res_id)
                        or model_icons.get(model)
                        or "/view_history/static/description/icon.png",
                        "is_client_action": True,
                        "action_id": res_id or False,
                        "action_tag": record.client_action_tag,
                        "action_params": record.client_action_params or {},
                        "action_context": record.client_action_context or {},
                        "action_path": record.client_action_path or False,
                        "action_target": record.client_action_target or False,
                    }
                )
                continue
            if res_id == 0:
                try:
                    target_model.check_access("read")
                except AccessError:
                    continue
                icon_url = model_icons.get(model)
                if not icon_url:
                    module_name = model_modules.get(model)
                    if module_name:
                        icon_url = f"/{module_name}/static/description/icon.png"
                if not icon_url:
                    icon_url = "/view_history/static/description/icon.png"
                item_data = {
                    "id": record.id,
                    "model": model,
                    "model_name": model_names.get(model, model),
                    "res_id": 0,
                    "display_name": model_names.get(model, model),
                    "viewed_at": record.viewed_at,
                    "icon_url": icon_url,
                    "is_list": True,
                }
                item_data.update(model_actions.get(model, {}))
                items.append(item_data)
                continue
            try:
                try:
                    target_model.check_access("read")
                    target = target_model.browse(res_id)
                    target.check_access("read")
                except AccessError:
                    continue
                if not target.exists():
                    continue
                icon_url = False
                for icon_field in ("type_icon", "icon", "image_1920", "image", "image_128", "subject_icon", "avatar_image"):
                    field_def = target._fields.get(icon_field)
                    if field_def and isinstance(field_def, (Image, Binary)) and target[icon_field]:
                        icon_url = f"/web/image/{model}/{res_id}/{icon_field}"
                        break
                if not icon_url:
                    icon_url = model_icons.get(model)
                if not icon_url:
                    module_name = model_modules.get(model)
                    if module_name:
                        icon_url = f"/{module_name}/static/description/icon.png"
                if not icon_url:
                    icon_url = "/view_history/static/description/icon.png"
                display_name = target.sudo().display_name
                if model == "account.move" and hasattr(target, "partner_id") and target.sudo().partner_id:
                    display_name = f"{display_name} - {target.sudo().partner_id.name}"
            except (MissingError, Exception):
                continue
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
