from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_cash_rounding_id = fields.Many2one(
        "account.cash.rounding",
    )