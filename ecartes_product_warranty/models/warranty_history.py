from odoo import api, fields, models

class WarrantyHistory(models.Model):
    _name = 'warranty.history'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Warranty History'

    name = fields.Char(string="Description")
    date = fields.Date(string="Date")
    warranty_start_date = fields.Date(string="Start Date")
    warranty_end_date = fields.Date(string="End Date")
    amt = fields.Float(string="Amount",default=0.0)
    is_paid = fields.Boolean(string="Is Paid")
    is_free = fields.Boolean(string="Is Free")
    is_renewed = fields.Boolean(string="Is Renewed")
    warranty_id = fields.Many2one(comodel_name="product.warranty", string="Warranty")
    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        copy=False, readonly=True, tracking=True,
        domain=[('move_type', '=', 'out_invoice')])
