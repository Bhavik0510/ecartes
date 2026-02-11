from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_warranty_invoice = fields.Boolean()
    warranty_id = fields.Many2one(comodel_name="product.warranty", string="Warranty")