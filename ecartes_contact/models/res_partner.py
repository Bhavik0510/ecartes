# -*- coding: utf-8 -*-

from odoo import models,fields ,api , _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_id = fields.Many2one('res.company', 'Company', index=True)

    # type_of_company = fields.Selection([('prospective_customer', 'Prospective Customer'),
    #                                     ('prospective_tender', 'Prospective Tender'),
    #                                     ('existing_client', 'Existing Client'),
    #                                     ('dealer', 'Dealer'),
    #                                     ('supplier', 'Supplier'),
    #                                     ('lost_company', 'Lost Company')],
    #                                     "Company Type",required=True
    #                                     )
    type_of_company = fields.Many2one('vx.type.of.company', string="Type of Company")

    # industry_type = fields.Selection([('banking_services', 'Banking & Financial Services'),
    #                                    ('government', 'Government - Defense & Security'),
    #                                     ('government_other', 'Government - Other ,MNC & Corporates'),
    #                                     ('solar', 'Solar'),
    #                                     ('education', 'Education'),
    #                                     ('hotels_enterainment', 'Hotels and Entertainment'),
    #                                     ('Power_energy', 'Power & Energy'),
    #                                     ('healthcare', 'Healthcare'),
    #                                     ('technology', 'Technology'),
    #                                     ('sme', 'SME'),
    #                                     ('other', 'Other')],
    #                                     "Industry Type",required=True
    #                                     )  
    industry_id = fields.Many2one("res.partner.industry", "Industry Type")
    gstin = fields.Char("GSTIN")
    fax = fields.Char('Fax')
    cin = fields.Char('CIN')
    # billing_address = fields.Text("Billing Address",required=True)
    
    # shipping_address = fields.Text("Shiping Address",required=True)
    # billing_city = fields.Char("Billing City",required=True)
    # shipping_city = fields.Char("Shiping City",required=True)
    # billing_state = fields.Many2one("res.country.state", string='Billing State',required=True)
    # shipping_state = fields.Many2one("res.country.state", string='Shipping State',required=True)

    # billing_zipcode = fields.Char("Billing Zipcode",required=True)
    # shipping_zipcode = fields.Char("Zipcode Zipcode",required=True)
    # billing_country = fields.Many2one("res.country","Billing Country" ,required=True)
    # shipping_country = fields.Many2one("res.country","Shipping Country",required=True)

    # @api.model
    # def default_get(self, default_fields):
    #     values = super().default_get(default_fields)
    #     if self.env.user.has_group('ecartes_contact.own_contacts_group'):
    #         values['user_id'] = self.env.user.id
    #     return values

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        # exiting_customer = self.env['res.partner'].sudo().search([]).filtered(lambda a:a.name == vals.get('name') and a.company_type == vals.get('company_type'))
        # if exiting_customer:
        #     raise ValidationError(_("This name's Contact already exits"))
        for rec in res:
            if rec.company_type == 'company' and self._context.get('is_company_create') == False:
                if rec.child_ids and rec.child_ids.filtered(lambda a:a.type == 'invoice'):
                    return res
                else:
                    raise ValidationError(_('You must have atleast one Invoice Address'))
        return res

    @api.constrains('name')
    def check_customer_exist(self):
        for rec in self:
            exiting_customer = self.env['res.partner'].search([]).filtered(lambda a:a.id != rec.id and a.name.lower().replace(' ', '') == rec.name.lower().replace(' ', ''))
            if exiting_customer:
                raise ValidationError(_("Contact already exits with this name !"))

    @api.onchange('phone', 'mobile', 'email')
    def onchange_contact_number(self):
        contact_id = False
        if self.mobile:
            contact_id = self.env['res.partner'].search(['|', ('mobile', '=', self.mobile), ('phone', '=', self.mobile)])
            if contact_id:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _("Contact already exits with this Mobile Number !")
                }}
        if self.phone:
            contact_id = self.env['res.partner'].search(['|', ('mobile', '=', self.phone), ('phone', '=', self.phone)])
            if contact_id:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _("Contact already exits with this Phone Number !")
                }}

        if self.email:
            contact_id = self.env['res.partner'].search([('email', '=', self.email)])
            if contact_id:
                return {'warning': {
                    'title': _('Warning!'),
                    'message': _("Contact already exits with this Email !")
                }}

    #
    # @api.model
    # def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
    #     if self.env.user.has_group('ecartes_contact.own_contacts_group'):
    #         # args = ['|',('user_id', '=', self.env.user.id),('user_id', '=', False)]
    #         args = [('company_id', 'in', self.env.user.company_ids.ids),('user_id', '=', self.env.user.id)]
    #     return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
    #
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if self.env.user.has_group('ecartes_contact.own_contacts_group'):
    #         # args = ['|',('user_id', '=', self.env.user.id),('user_id', '=', False)]
    #         args = [('company_id', 'in', self.env.user.company_ids.ids),('user_id', '=', self.env.user.id)]
    #     return super()._name_search(name=name, args=args, operator=operator,limit=limit,name_get_uid=name_get_uid)
    #

class ResCompany(models.Model):
    _inherit = 'res.company'


    fax = fields.Char('Fax')
    cin = fields.Char('CIN')



