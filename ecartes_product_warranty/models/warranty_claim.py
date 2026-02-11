from odoo import api, fields, models
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError


class WaarantyClaim(models.Model):
    _name = 'warranty.claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'claim_description'
    _description = 'Warranty Claim'

    claim_description = fields.Char(string="Claim Description", required=True)
    claim_date = fields.Date(string="Claim Date", required=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, check_company=True,
                              readonly=True)
    deadline_date = fields.Date(string="Deadline Date")
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True,
        default=lambda self: self.env.company)
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, check_company=True, change_default=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'Low'), ('2', 'Urgent'), ('3', 'Very High')], default='0',
                                string="Priority")

    state = fields.Selection(string="Status", selection=[('new', 'New'), ('confirm', 'Confirm'), ('under_maintenance', 'Under Maintenance'),
                                                         ('ready_to_deliver', 'Ready To Deliver'), ('done', 'Done')],
                             default="new")
    warranty_id = fields.Many2one(comodel_name="product.warranty", string="Warranty")
    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('is_under_warranty','=',True),('type', 'in', ['product', 'consu']), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        required=True, check_company=True)

    lot_ids = fields.Many2many(
        'stock.lot', string='Lot/Serial',
        domain="[('product_id','=', product_id), ('company_id', '=', company_id)]", check_company=True)

    product_qty = fields.Float(
        'Product Quantity',
        default=1.0,
        readonly=True, required=True) #, states={'draft': [('readonly', False)]})
    tracking = fields.Selection(string='Product Tracking', related="product_id.tracking", readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(WaarantyClaim, self).create(vals_list)
        domain = []
        for rec in res:
            if rec.product_id.type_of_claim == 'limited':
                claim_limit = rec.product_id.no_of_claim
                if rec.tracking in ['serial', 'lot']:
                    domain+= [('product_id','=',rec.product_id.id)]
                    domain+= [('lot_id','=',rec.lot_id.id)]
                else:
                    domain += [('product_id', '=', rec.product_id.id)]
                record = self.search_count(domain)
                if record > claim_limit:
                    raise UserError('You have exceeded the maximum claim limit for this product.')
        return res

    @api.onchange('warranty_id')
    def onchnage_warranty(self):
        self.product_id = self.warranty_id.product_id
        self.lot_ids = self.warranty_id.lot_id
        self.partner_id = self.warranty_id.partner_id

    def under_maintenance(self):
        self.state = 'under_maintenance'

    def ready_to_deliver(self):
        self.state = 'ready_to_deliver'

    def done(self):
        self.state = 'done'

    def confirm_claim(self):
        if self.warranty_id.state == 'expired' and not self.env.user.has_group('ecartes_product_warranty.allow_claim_forcefully'):
            raise ValidationError('Your product is expired ')
        else:
            self.state = 'confirm'
