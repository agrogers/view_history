from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    log_view_history = fields.Boolean(
        string="Log View History",
        default=True,
        help="Enable to store a history entry when you open a form view.",
    )
