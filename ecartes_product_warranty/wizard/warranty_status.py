
from odoo import models, fields, api

class WarrantyStatus(models.TransientModel):
    _name = 'warranty.status'
    _description = 'Bulk Update Warranty Status'

    state = fields.Selection([
        ('draft', 'New'),
        ('2beinvoice', 'To Be invoice'),
        ('invoiced', 'Invoiced'),
        ('under_warranty', 'Under Warranty'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled')
    ], required=True, string="State")

    def action_apply_state(self):
        active_ids = self.env.context.get('active_ids', [])
        warranties = self.env['product.warranty'].browse(active_ids)
        warranties.write({'state': self.state})
        return {'type': 'ir.actions.act_window_close'}
