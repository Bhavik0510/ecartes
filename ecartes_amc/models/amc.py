from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import pandas as pd


class Amc(models.Model):
    _name = 'amc.amc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Amc'
    _rec_name = 'name'

    name = fields.Char('Reference', default='New', copy=False, required=True, readonly=True)
    description = fields.Char('Description', tracking=True)
    amc_type = fields.Selection(string="AMC Type", selection=[('camc', 'CAMC'), ('namc', 'NAMC'), ], required=True,
                                default="camc", tracking=True)
    amc_cost = fields.Selection(string="AMC Cost", selection=[('free', 'Free'), ('paid', 'Paid'), ], required=True,
                                default="free", tracking=True)
    invoice_term = fields.Selection(string="Invoice Term", tracking=True,
                                    selection=[('quarterly', 'Quarterly'), ('halfyearly', 'Half Yearly'),
                                               ('annually', 'Annually'), ], default="annually")

    state = fields.Selection([
        ('draft', 'New'),
        ('2beinvoice', 'To Be invoice'),
        ('invoiced', 'Invoiced'),
        ('under_amc', 'Under AMC'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('cancel', 'Cancelled')], string='Status',
        copy=False, default='draft', readonly=True, tracking=True, )

    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, check_company=True, change_default=True, tracking=True)
    responsible_person = fields.Char(string='Contact Person', tracking=True)
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

    # sale_order_id = fields.Many2one('sale.order', 'Sale Order', copy=False)
    user_id = fields.Many2one('res.users', string="Sales Person", default=lambda self: self.env.user, check_company=True)
    renewal_user_id = fields.Many2one('res.users', string="Renewal By", default=lambda self: self.env.user,
                                      check_company=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True,
        default=lambda self: self.env.company)

    amc_claim_ids = fields.One2many(comodel_name="amc.claim", inverse_name="amc_id", string="Claims History", tracking=True)
    amc_start_date = fields.Date(string="Amc Start Date", default=datetime.today(), tracking=True)
    amc_end_date = fields.Date(string="Amc End Date", tracking=True)
    amc_term_id = fields.Many2one(comodel_name="amc.term", string="Amc Term", tracking=True)
    # warranty_history_ids = fields.One2many(comodel_name="warranty.history", inverse_name="warranty_id",
    #                                      string="Warranty History")
    renew_date = fields.Char(string="Renew Date", tracking=True)
    amc_amt = fields.Float(string="Amount", tracking=True)
    is_renewed = fields.Boolean('Renewed', copy=False, readonly=True, tracking=True)
    # allow_renewal = fields.Boolean(string="Allow Renewal", related="product_id.allow_renewal")

    # invoice_fields
    invoice_id = fields.Many2one(
        'account.move', 'Invoice',
        copy=False, readonly=True, tracking=True,
        domain=[('move_type', '=', 'out_invoice')])
    invoice_state = fields.Selection(string='Invoice State', related='invoice_id.state')
    invoiced = fields.Boolean('Invoiced', copy=False, readonly=True)

    line_ids = fields.One2many(comodel_name="amc.line", inverse_name="amc_id")
    amc_history_ids = fields.One2many(comodel_name="amc.history", inverse_name="amc_id")
    claim_count = fields.Integer(compute='compute_claim_count')
    amc_line_ids = fields.One2many(comodel_name="amc.line", inverse_name="amc_id")

    amc_visitor_plan_ids = fields.One2many("amc.visitor", "amc_id", 'Visitor Plan')
    invoice_ids = fields.Many2many('account.move', string="Invoices")
    invoice_count = fields.Integer(compute='_compute_invoice_count')
    total_amc_amount = fields.Float(string='Total Amount', tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        tracking=True,
        required=True,
        related='company_id.currency_id', store=True, readonly=False
    )

    # warranty_ids = fields.Many2many(
    #     comodel_name="product.warranty",
    #     string="Warranty",

    #     compute="_compute_warranty_ids",
    # )

    _sql_constraints = [
        ('name', 'unique (name)', 'The name of the Warranty must be unique!'),
    ]

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for records in self:
            records.invoice_count = len(records.invoice_ids)

    @api.onchange('amc_amt')
    def _onchange_amc_amt(self):
        self.total_amc_amount = self.amc_amt

    @api.onchange('invoice_term')
    def _onchange_invoice_term(self):
        if self.invoice_term == 'halfyearly':
            tmp = []
            today = self.amc_start_date
            td = timedelta(days=182)
            half_yearly_date = today, today + td
            for rec in half_yearly_date:
                tmp.append((0, 0, {'visit_date': rec}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp



        elif self.invoice_term == 'quarterly':
            tmp = []
            td = timedelta(days=91)
            q1 = self.amc_start_date
            q2 = q1 + td
            q3 = q2 + td
            q4 = q3 + td
            quarterly = q1, q2, q3, q4
            for rec in quarterly:
                tmp.append((0, 0, {'visit_date': rec}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp

        elif self.invoice_term == 'annually':
            tmp = []
            today = self.amc_start_date
            td = timedelta(days=182)
            annually_date = today + td
            tmp.append((0, 0, {'visit_date': annually_date}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for records in self:
            records.invoice_count = len(records.invoice_ids)

    @api.onchange('amc_amt')
    def _onchange_amc_amt(self):
        self.total_amc_amount = self.amc_amt

    @api.onchange('invoice_term')
    def _onchange_invoice_term(self):
        if self.invoice_term == 'halfyearly':
            tmp = []
            today = self.amc_start_date
            td = timedelta(days=182)
            half_yearly_date = today, today + td
            for rec in half_yearly_date:
                tmp.append((0, 0, {'visit_date': rec}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp



        elif self.invoice_term == 'quarterly':
            tmp = []
            td = timedelta(days=91)
            q1 = self.amc_start_date
            q2 = q1 + td
            q3 = q2 + td
            q4 = q3 + td
            quarterly = q1, q2, q3, q4
            for rec in quarterly:
                tmp.append((0, 0, {'visit_date': rec}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp

        elif self.invoice_term == 'annually':
            tmp = []
            today = self.amc_start_date
            td = timedelta(days=182)
            annually_date = today + td
            tmp.append((0, 0, {'visit_date': annually_date}))
            self.amc_visitor_plan_ids = [(6, 0, [])]
            self.amc_visitor_plan_ids = tmp

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('amc.amc.seq') or _('New')

            # print("############################################",vals)
            # pw = self.search([('product_id', '=', vals.get('line_ids.product_id')), ('lot_id', '=', vals.get('line_ids.lot_id'))]).ids
            # if len(pw) > 0:
            #     raise UserError('You Cannot Create more than one Warranty with same serial number.')

        super(Amc, self).create(vals_list)

    @api.onchange('amc_term_id', 'amc_start_date')
    def onchnage_amc_term(self):
        if self.amc_term_id.amc_by == 'year':
            end_date = self.amc_start_date + relativedelta(years=self.amc_term_id.total_no_of) - timedelta(days=1)
            self.amc_end_date = end_date
        if self.amc_term_id.amc_by == 'month':
            end_date = self.amc_start_date + relativedelta(months=self.amc_term_id.total_no_of) - timedelta(days=1)
            self.amc_end_date = end_date
        if self.amc_term_id.amc_by == 'day':
            end_date = self.amc_start_date + relativedelta(days=self.amc_term_id.total_no_of) - timedelta(days=1)
            self.amc_end_date = end_date

    def confirm_amc(self):
        if self.amc_cost == 'free':
            self.state = 'under_amc'

            self.amc_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'amc_start_date': self.amc_start_date,
                'amc_end_date': self.amc_end_date,
                'amt': self.amc_amt,
                'is_paid': True if self.amc_type == 'paid' else False,
                'is_free': True if self.amc_type == 'free' else False,
            })]

        else:

            self.state = '2beinvoice'   


    def create_amc_invoice(self):
        for amc in self:
            invoices = amc._create_invoices(amc_id=amc.id, amc_name=amc.name, invoice_amount=self.amc_amt)

            if invoices:
                self.invoice_ids = [(6, 0, invoices)]
                self.state = 'invoiced'

        return True

    def _create_invoices(self, amc_id=False, amc_name=False, move_type='out_invoice', invoice_amount=None,
                         currency_id=None,
                         partner_id=None,
                         date_invoice=None, payment_term_id=False, auto_validate=False):

        if self.invoice_term == "quarterly":
            invoice_amount = self.amc_amt / 4
        elif self.invoice_term == "halfyearly":
            invoice_amount = self.amc_amt / 2
        elif self.invoice_term == "annually":
            invoice_amount = self.amc_amt
        else:
            pass


        invoices = []
        for record in self.amc_visitor_plan_ids:
            date_invoice = record.visit_date


            invoice_vals = {
                'move_type': move_type,
                'partner_id': partner_id or self.partner_id.id,
                'invoice_date': date_invoice,
                'is_amc_invoice': True,
                'date': date_invoice,
                'amc_id': amc_id,
                'invoice_line_ids': [(0, 0, {
                    'name': 'AMC %s' % amc_name,
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
            invoices.append(invoice.id)
        return invoices

    def action_created_invoice(self):
        self.ensure_one()
        return {
            'name': _('Invoice created'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            # 'view_id': self.env.ref('account.view_move_tree').id,
            'target': 'current',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }

    def renew_amc(self):
        data = {
            'default_amc_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_amc_term_id': self.amc_term_id.id,
            'default_amc_start_date': self.amc_start_date,
            'default_amc_end_date': self.amc_end_date,
            # 'default_line_ids':[(6,0,self.line_ids.ids)],
            # 'default_line_ids':[(0,0,{'product_id': rec.product_id.id,'lot_id': rec.lot_id.id,
            #                         'product_qty': rec.product_qty}) for rec in self.line_ids]
        }
        return {
            'name': 'AMC Renewal',
            'type': 'ir.actions.act_window',
            'res_model': 'amc.renew',
            'view_mode': 'form',
            'target': 'new',
            "context": data,
        }

    def _check_amc_cron(self):

        prod_amc = self.env['amc.amc'].search([('state', '=', 'under_amc')])

        for amc in prod_amc:
            sevendays_before = amc.amc_end_date + timedelta(days=-7)
            if datetime.today().date() == sevendays_before:
                emi_cc = []
                mail_to = amc.partner_id.email
                mail_values = {
                    'subject': 'Remider For Renewal AMC',
                    'body_html': '<p style="font-weight:700"> Greetings from ' + amc.company_id.name + '</p>'
                                                                                                       '<p style="font-weight:700"> As your  ' + amc.name + '</p>'
                                                                                                                                                            '<p style="font-weight:700"> AMC ' + amc.product_id.name + '</p'
                                                                                                                                                                                                                       '<p style="font-weight:700"> Going to expire on ' + str(
                        amc.amc_end_date) + '</p>'
                                            '</br> </br> </br> <p style="font-weight:500">Note :  This is System generated Test Email ',
                    'email_from': self.env.user.company_id.partner_id.email,
                    'email_to': mail_to,
                    # 'email_cc': ", ".join(emi_cc),
                }
                self.env['mail.mail'].sudo().create(mail_values).sudo().send()
            if amc.amc_end_date < datetime.today().date():
                amc.state = 'expired'

    def compute_claim_count(self):
        for record in self:
            record.claim_count = self.env['amc.claim'].search_count(
                [('amc_id', '=', self.id)])

    def get_amc(self):
        self.ensure_one()
        return {
            'name': _('Claims'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'amc.claim',
            'domain': [('amc_id', '=', self.id)],
            'context': "{'create': False}"
        }   

    def create_amc_claim(self):
        if self.state == 'expired' and not self.env.user.has_group('ecartes_amc.allow_claim_forcefully'):
            raise ValidationError('Your amc is expired ')
        else:
            # self.write({'state': 'under_amc'})
            data = {
                'default_amc_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amc_line_ids': [(6, 0, self.amc_line_ids.ids)],
            }
            return {
                'name': 'AMC Renewal',
                'res_model': 'amc.claim',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': self.env.ref("ecartes_amc.amc_claim_form_view").id,
                'target': 'new',
                "context": data,
            }


    def create_amc_claim_renew_state(self):
        pass

    def start_amc(self):
        if self.is_renewed == False:
            self.state = 'under_amc'

            self.amc_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'amc_start_date': self.amc_start_date,
                'amc_end_date': self.amc_end_date,
                'amt': self.amc_amt,
                'is_paid': True if self.amc_type == 'paid' else False,
                'is_free': True if self.amc_type == 'free' else False,
                'invoice_id': self.invoice_id.id or False,
            })]
        elif self.is_renewed == True:
            self.state = 'renewed'

            self.amc_history_ids = [(0, 0, {
                'name': self.name,
                'date': datetime.today(),
                'amc_start_date': self.amc_start_date,
                'amc_end_date': self.amc_end_date,
                'amt': self.amc_amt,
                'is_paid': True if self.amc_type == 'paid' else False,
                'is_free': True if self.amc_type == 'free' else False,
                'is_renewed': True if self.amc_type == 'paid' else False,
                'invoice_id': self.invoice_id.id,
            })]


    def get_amc_visitors(self):
        email_to = []
        amc_confirm = self.env['amc.amc'].search([('state', '=', 'under_amc')]).mapped('id')
        if amc_confirm:
            visitors = self.env['amc.visitor'].search([('amc_id', 'in', amc_confirm)])
            for rec in visitors:

                visit = rec.visit_date - timedelta(days=7)
                if datetime.today().date() == visit:
                    if rec.engineer_id and rec.engineer_id.work_email:
                        email_to.append(rec.engineer_id.work_email)
                    if rec.amc_id.user_id and rec.amc_id.user_id.partner_id.email:
                        email_to.append(rec.amc_id.user_id.partner_id.email)
                    mail_values = {
                        'subject': 'Reminder For Visit AMC',
                        'email_from': self.env.user.partner_id.email,
                        'email_to': email_to,
                        'author_id': self.env.user.partner_id.id
                    }
                    self.env['mail.mail'].create(mail_values).send()
