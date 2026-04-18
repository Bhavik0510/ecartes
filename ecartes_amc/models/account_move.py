from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Keep this field in ecartes_amc as well so AMC views/actions never crash
    # even if another module that also defines it is not loaded in the registry.
    is_amc_invoice = fields.Boolean(
        string="AMC Invoice",
        default=False,
        copy=False,
    )
    amc_id = fields.Many2one(comodel_name="amc.amc", string="AMC")
