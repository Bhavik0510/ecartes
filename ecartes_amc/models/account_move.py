from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_amc_invoice = fields.Boolean()
    amc_id = fields.Many2one(comodel_name="amc.amc", string="AMC")