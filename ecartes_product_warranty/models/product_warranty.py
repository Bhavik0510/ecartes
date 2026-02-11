from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from odoo.exceptions import UserError, ValidationError


class ProductWarranty(models.Model):
    _name = 'product.warranty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'product_warranty'
    _rec_name = 'name'

    name = fields.Char('Reference', default='New', copy=False, required=True, readonly=True)

    description = fields.Char('Product Warranty Description', tracking=True)
    warranty_type = fields.Selection(string="Warranty Type", selection=[('free', 'Free'), ('paid', 'Paid'), ],
                                     required=True, default="free", tracking=True)

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('is_under_warranty','=',True),('type', 'in', ['product', 'consu']), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        readonly=True, required=True, check_company=True, tracking=True)

    lot_ids = fields.Many2many(
        'stock.lot', string='Lot/Serial', tracking=True,
        domain="[('product_id','=', product_id), ('company_id', '=', company_id)]", check_company=True)

    product_qty = fields.Float(
        'Product Quantity',
        default=1.0,
        readonly=True, required=True) #, states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'New'),
        ('2beinvoice', 'To Be invoice'),
        ('invoiced', 'Invoiced'),
        ('under_warranty', 'Under Warranty'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('cancel', 'Cancelled')], string='Status',
        copy=False, default='draft', readonly=True, tracking=True )

    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, check_company=True, change_default=True, tracking=True)

    email = fields.Char(related="partner_id.email")
    phone = fields.Char(related="partner_id.phone")
    mobile = fields.Char(related="partner_id.mobile")
    street = fields.Char(related="partner_id.street")
    street2 = fields.Char(related="partner_id.street2")
    zip = fields.Char(change_default=True, related="partner_id.zip")
    city = fields.Char(related="partner_id.city")
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]", related="partner_id.state_id")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', related="partner_id.country_id")

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', copy=False)
    user_id = fields.Many2one('res.users', string="Sales Person", default=lambda self: self.env.user, check_company=True)
    renewal_user_id = fields.Many2one('res.users', string="Renewal By", default=lambda self: self.env.user,
                                      check_company=True)
    renew_date = fields.Char(string="Renew Date", tracking=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True, tracking=True,
        default=lambda self: self.env.company)
    tracking = fields.Selection(string='Product Tracking', related="product_id.tracking", readonly=False)
    warranty_claim_ids = fields.One2many(comodel_name="warranty.claim", inverse_name="warranty_id",
                                         string="Claims History")
    warranty_start_date = fields.Date(string="Warranty Start Date", default=datetime.today(), tracking=True)
    installation_date = fields.Date(string="Installation Date", tracking=True, copy=False)
    is_set_install_date = fields.Boolean(string="Set Installation Date?", default=False, tracking=True, copy=False)
    warranty_end_date = fields.Date(string="Warranty End Date", tracking=True)
    warranty_term_id = fields.Many2one(comodel_name="warranty.term", string="Warranty Term", tracking=True)
    warranty_history_ids = fields.One2many(comodel_name="warranty.history", inverse_name="warranty_id",
                                           string="Warranty History")
    warranty_amt = fields.Float(string="Amount", tracking=True)
    is_renewed = fields.Boolean('Renewed', copy=False, readonly=True, tracking=True)
    allow_renewal = fields.Boolean(string="Allow Renewal", related="product_id.allow_renewal")
    claim_count = fields.Integer(compute='compute_claim_count')
    amc_count = fields.Integer(compute='compute_amc_count')
    # invoice_fields
    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        copy=False, readonly=True, tracking=True,
        domain=[('move_type', '=', 'out_invoice')])
    invoice_state = fields.Selection(string='Invoice State', related='invoice_id.state')
    invoiced = fields.Boolean('Invoiced', copy=False, readonly=True, tracking=True)
    sale_id = fields.Many2one(comodel_name="sale.order", related="invoice_id.order_id", string="Sale")

    _sql_constraints = [
        ('name', 'unique (name)', 'The name of the Warranty must be unique!'),
        ('installation_date_check', 
         'CHECK (installation_date >= warranty_start_date)', 
         'Installation Date cannot be earlier than the Warranty Start Date!')
    ]

    @api.constrains('warranty_start_date')
    def _check_warranty_date_permission(self):
        for order in self:
            if self.env.user not in order.env.ref('ecartes_product_warranty.allow_warranty_configurration').users:
                raise UserError("You do not have permission to edit this field.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('product.warranty.seq') or _('New')

            if vals.get('lot_id'):
                pw = self.search([('product_id', '=', vals.get('product_id')), ('lot_id', '=', vals.get('lot_id'))]).ids
                if len(pw) > 0:
                    raise UserError('You Cannot Create more than one Warranty with same serial number.')
            if vals.get('installation_date'):
                vals.update({'is_set_install_date': True})

        return super(ProductWarranty, self).create(vals_list)

    def write(self, vals):
        if vals.get('installation_date'):
            vals.update({'is_set_install_date': True})
        return super(ProductWarranty, self).write(vals)

    @api.onchange('warranty_term_id', 'installation_date')
    def onchnage_warranty_term(self):
        end_date = ''
        if self.warranty_term_id.warranty_by == 'year':
            end_date = self.warranty_start_date + relativedelta.relativedelta(years=self.warranty_term_id.total_no_of)
        elif self.warranty_term_id.warranty_by == 'month':
            end_date = self.warranty_start_date + relativedelta.relativedelta(months=self.warranty_term_id.total_no_of)
        elif self.warranty_term_id.warranty_by == 'day':
            end_date = self.warranty_start_date + relativedelta.relativedelta(days=self.warranty_term_id.total_no_of)
        if self.installation_date:
            installation_day = self.installation_date - self.warranty_start_date
            end_date = end_date + relativedelta.relativedelta(days=installation_day.days)
        self.warranty_end_date = end_date

    def confirm_warranty(self):
        if self.warranty_type == 'free':
            self.state = 'under_warranty'

            self.warranty_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'warranty_start_date': self.warranty_start_date,
                'warranty_end_date': self.warranty_end_date,
                'amt': self.warranty_amt,
                'is_paid': True if self.warranty_type == 'paid' else False,
                'is_free': True if self.warranty_type == 'free' else False,
            })]

        else:
            self.state = '2beinvoice'

    def create_warranty_invoice(self):
        for warranty in self:
            invoice = warranty._create_invoices(warrnty_id=warranty.id,warrnty_name=warranty.name,invoice_amount=self.warranty_amt)
            if invoice:
                self.invoice_id = invoice
                self.state = 'invoiced'

        return True

    # def renew_warranty(self):

    #     data = {
    #         'default_warranty_id': self.id,
    #         'default_product_id': self.product_id.id,
    #         'default_lot_id': self.lot_id.id,
    #         'default_product_qty': self.product_qty,
    #         'default_partner_id': self.partner_id.id,
    #     }
    #     return {
    #         'name': 'Warranty Renewal',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'product.warranty.renew',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         "context": data,
    #     }

    def _create_invoices(self, warrnty_id=False,warrnty_name=False, move_type='out_invoice', invoice_amount=None, currency_id=None,
                         partner_id=None,
                         date_invoice=None, payment_term_id=False, auto_validate=False):

        date_invoice = datetime.today()

        invoice_vals = {
            'move_type': move_type,
            'partner_id': partner_id or self.partner_id.id,
            'invoice_date': date_invoice,
            'is_warranty_invoice': True,
            'date': date_invoice,
            'warranty_id': warrnty_id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Warranty %s' % warrnty_name,
                'quantity': 1,
                'price_unit': invoice_amount,
                'tax_ids': [(6, 0, [])],
            })]
        }

        if payment_term_id:
            invoice_vals['invoice_payment_term_id'] = payment_term_id

        if currency_id:
            invoice_vals['currency_id'] = currency_id

        invoice = self.env['account.move'].with_context(default_move_type=move_type).create(invoice_vals)
        return invoice

    def action_created_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice created'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
            'res_id': self.invoice_id.id,
        }

    def _check_product_warranty_cron(self):
        prod_warranty = self.env['product.warranty'].search([('state', '=', 'under_warranty')])


        for warranty in prod_warranty:
            sevendays_before = warranty.warranty_end_date + timedelta(days=-7)
            if datetime.today().date() == sevendays_before:
                emi_cc = []
                mail_to = warranty.partner_id.email
                mail_values = {
                    'subject': 'Remider For Renewal Product Warranty',
                    'body_html':'<p style="font-weight:700"> Greetings from ' + warranty.company_id.name + '</p>'
                                 '<p style="font-weight:700"> As your  ' + warranty.name + '</p>'
                                 '<p style="font-weight:700"> Product Warranty ' + warranty.product_id.name + '</p'
                                 '<p style="font-weight:700"> Going to expire on ' + str(warranty.warranty_end_date) +'</p>'
                                 '</br> </br> </br> <p style="font-weight:500">Note :  This is System generated Test Email ',
                    'email_from': self.env.user.company_id.partner_id.email,
                    'email_to': mail_to,
                    # 'email_cc': ", ".join(emi_cc),
                }
                self.env['mail.mail'].sudo().create(mail_values).sudo().send()

            if warranty.warranty_end_date < datetime.today().date():
                warranty.state = 'expired'

    def start_warranty(self):
        if self.invoice_state == 'posted' and self.is_renewed == False:
            self.state = 'under_warranty'

            self.warranty_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'warranty_start_date': self.warranty_start_date,
                'warranty_end_date': self.warranty_end_date,
                'amt': self.warranty_amt,
                'is_paid': True if self.warranty_type == 'paid' else False,
                'is_free': True if self.warranty_type == 'free' else False,
                'invoice_id': self.invoice_id.id or False,
            })]
        elif self.is_renewed == True and self.invoice_state == 'posted':
            self.state = 'renewed'

            self.warranty_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'warranty_start_date': self.warranty_start_date,
                'warranty_end_date': self.warranty_end_date,
                'amt': self.warranty_amt,
                'is_paid': True if self.warranty_type == 'paid' else False,
                'is_free': True if self.warranty_type == 'free' else False,
                'is_renewed': True if self.warranty_type == 'paid' else False,
                'invoice_id': self.invoice_id.id,
            })]
        else:
            raise ValidationError('Please Confirm the Invoice')

    def compute_claim_count(self):
        for record in self:
            record.claim_count = self.env['warranty.claim'].search_count(
                [('warranty_id', '=', self.id)])


    def get_warranty(self):
        self.ensure_one()
        return {
            'name': _('Created Warranty'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'warranty.claim',
            'domain': [('warranty_id', '=', self.id)],
            'context': "{'create': False}"
        }


    def create_warranty_claim(self):

        if self.product_id.type_of_claim == 'limited':
            claim_limit = self.product_id.no_of_claim

            if self.claim_count >= claim_limit:
                raise UserError('You have exceeded the maximum claim limit for this product.')

            else:
                self.write({'state': 'under_warranty'})
                data = {
                    'default_warranty_id': self.id,
                    'default_product_id': self.product_id.id,
                    'default_lot_ids': self.lot_ids.ids,
                    'default_product_qty': self.product_qty,
                    'default_partner_id': self.partner_id.id,
                }
        else:
            self.write({'state': 'under_warranty'})
            data = {
                'default_warranty_id': self.id,
                'default_product_id': self.product_id.id,
                'default_lot_ids': self.lot_ids.ids,
                'default_product_qty': self.product_qty,
                'default_partner_id': self.partner_id.id,
            }
        return {
            'name': 'Warranty Renewal',
            'res_model': 'warranty.claim',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref("ecartes_product_warranty.warranty_claim_form_view").id,
            'target': 'new',
            "context": data,

        }

    def unlink(self):
        for rec in self:
            if rec.state == 'under_warranty':
                raise UserError("You can not delete warranty which is in under warranty, you must cancel it.")
        return super(ProductWarranty, self).unlink()

    def btn_cancel(self):
        self.state = 'cancel'

    def create_amcs(self):
        amc_term = None


        amc_term_exist = self.env['amc.term'].search([('amc_by','=',self.warranty_term_id.warranty_by),('total_no_of','=',self.warranty_term_id.total_no_of)])
        if amc_term_exist:
            amc_term = amc_term_exist.id
        else:
            vals = {
                'name':self.warranty_term_id.name,
                'amc_by':self.warranty_term_id.warranty_by,
                'total_no_of':self.warranty_term_id.total_no_of,
            }

            amc_id = self.env['amc.term'].sudo().create(vals)
            amc_term = amc_id.id

        line_lst1 = []
        for rec in self:
            line_lst1.append(rec.id) 

        new_amc = self.env['amc.amc'].sudo().create({
            'amc_term_id': amc_term or 1,
            'amc_start_date':self.warranty_start_date,
            'amc_cost':self.warranty_type,
            'product_warrenty_ids': line_lst1,
            # 'state':self.state,
            # 'amc_type':'namc',
            'partner_id': self.partner_id.id,
            # 'amc_end_date': self.warranty_end_date,
            'amc_amt': self.warranty_amt,
            'renewal_user_id':self.renewal_user_id.id,
            'line_ids': [
                    (0, 0, {
                        'product_id': self.product_id.id,
                        'product_qty': self.product_qty,
                        'lot_id': self.lot_id.id,
                    })
                ],  
        })
        new_amc._onchange_invoice_term()
        amc=self.env['amc.amc'].sudo().search([('product_warrenty_ids','in',self.id)])
        self.sale_id.amc_id=amc[0].id
    
    def get_amc(self):
        self.ensure_one()
        return {
            'name': _('AMC'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'amc.amc',
            'domain': [('product_warrenty_ids', 'in', self.id)],
            # 'context': "{'create': False}"
        }

    def compute_amc_count(self):
        for record in self:
            record.amc_count = self.env['amc.amc'].search_count(
                [('product_warrenty_ids', 'in', self.id)])


    def create_amc(self):

        check_invoices = self.mapped('invoice_id').ids
        if len(check_invoices) > 1:
            raise ValidationError(
                _("you can't create amc for differnt invoices warranty please select same invoice warranty"))
        else:

            line_lst = []
            for rec in self:
                line_lst.append((0, 0, {
                    'product_id': rec.product_id.id,
                    'lot_id': rec.lot_id.id,
                    'product_qty': rec.product_qty,
                }))
            
            line_lst1 = []
            for rec in self:
                line_lst1.append(rec.id)    
            
                
            amc_term = None
            amc_term_exist = self.env['amc.term'].search([('amc_by','=','year'),('total_no_of','=', 1)])
            if amc_term_exist:
                amc_term = amc_term_exist.id


                vals = {
                    'partner_id': self.mapped('partner_id').id,
                    'invoice_id': self.mapped('invoice_id').id,
                    'amc_term_id': amc_term,
                    'product_warrenty_ids': line_lst1,
                    'line_ids': line_lst,
                }
                amc = self.env['amc.amc'].create(vals)
                amc.onchnage_amc_term()
                amc._onchange_invoice_term()

        amc=self.env['amc.amc'].sudo().search([('product_warrenty_ids','in',line_lst1)])
        self.sale_id.amc_id=amc[0].id
    
    @api.model
    def _expire_warranties(self):
        """
        Scheduled job to update the status of warranties to 'expired' if the warranty_end_date is passed.
        """
        today = datetime.today().date()
        warranties = self.search([('warranty_end_date', '<', today), ('state', '=', 'under_warranty')])
        
        for warranty in warranties:
            warranty.write({'state': 'expired'})
            # _logger.info(f"Warranty {warranty.id} status updated to 'expired'")

    
