
from odoo import api, fields, models,_
from datetime import datetime
from dateutil import relativedelta

class ProductWarrantyRenew(models.TransientModel):
    _name = "product.warranty.renew"
    _description = 'Product Warranty Renew'

    warranty_id = fields.Many2one(comodel_name="product.warranty", string="Warranty")
    product_id = fields.Many2one(
        'product.product', string='Product',
    )

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial',
        domain="[('product_id','=', product_id)]")

    product_qty = fields.Float(
        'Product Quantity',
        default=1.0,
        )

    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        )

    warranty_start_date = fields.Date(string="Warranty Start Date", default=datetime.today())
    warranty_end_date = fields.Date(string="Warranty End Date")
    warranty_term_id = fields.Many2one(comodel_name="warranty.term", string="Warranty Term")
    renewal_amt = fields.Float(string="Renewal Amount")
    renewal_user_id = fields.Many2one('res.users', string="Renewal By", default=lambda self: self.env.user,
                                     )


    @api.onchange('warranty_term_id')
    def onchnage_warranty_term(self):
        if self.warranty_term_id.warranty_by == 'year':
            end_date = self.warranty_start_date + relativedelta.relativedelta(years=self.warranty_term_id.total_no_of)
            self.warranty_end_date = end_date
        if self.warranty_term_id.warranty_by == 'month':
            end_date = self.warranty_start_date + relativedelta.relativedelta(months=self.warranty_term_id.total_no_of)
            self.warranty_end_date = end_date
        if self.warranty_term_id.warranty_by == 'day':
            end_date = self.warranty_start_date + relativedelta.relativedelta(days=self.warranty_term_id.total_no_of)
            self.warranty_end_date = end_date

    def btn_save(self):
        self.warranty_id.write({
            'warranty_start_date':self.warranty_start_date,
            'warranty_end_date':self.warranty_end_date,
            'warranty_term_id':self.warranty_term_id.id,
            'warranty_type':'paid',
            'warranty_amt':self.renewal_amt,
            'is_renewed':True,
            'renew_date':datetime.today().date(),
            'state':'2beinvoice',
            'renewal_user_id':self.renewal_user_id.id,

        })
