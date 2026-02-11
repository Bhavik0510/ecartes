from odoo import api, fields, models

class AmcHistory(models.Model):
    _name = 'amc.history'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Amc History'

    name = fields.Char(string="Description")
    date = fields.Date(string="Date")
    amc_start_date = fields.Date(string="Start Date")
    amc_end_date = fields.Date(string="End Date")
    amt = fields.Float(string="Amount",default=0.0)
    is_paid = fields.Boolean(string="Is Paid")
    is_free = fields.Boolean(string="Is Free")
    is_renewed = fields.Boolean(string="Is Renewed")
    amc_id = fields.Many2one(comodel_name="amc.amc", string="AMC")
    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        copy=False, readonly=True, tracking=True,
        domain=[('move_type', '=', 'out_invoice')])
