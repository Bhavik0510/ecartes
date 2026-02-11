from odoo import models, fields, api,_
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError

class AmcLine(models.Model):
    _name = 'amc.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Amc Line'

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('is_under_amc','=',True),'|', ('company_id', '=', company_id), ('company_id', '=', False)]",
         check_company=True)

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial',
        domain="[('product_id','=', product_id), ('company_id', '=', company_id)]", check_company=True)

    product_qty = fields.Float(
        'Product Quantity',
        default=1.0,
        )
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True,
        default=lambda self: self.env.company)

    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string='Product Tracking', readonly=False)

    amc_id = fields.Many2one('amc.amc')
    amc_claim_id = fields.Many2one('amc.claim')
    currency_id = fields.Many2one(related='company_id.currency_id', depends=['company_id.currency_id'], store=True, string='Currency')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.tracking = self.product_id.tracking
