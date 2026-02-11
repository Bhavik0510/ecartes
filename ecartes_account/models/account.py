from odoo import models,fields ,api


class Account(models.Model):
    _inherit ='account.move'

 
    shipping_mode = fields.Selection([('not_selected','Not Selected'),
                                ('by_air','By Air'),
                                ('by_hand','By Hand'),
                                ('by_cargo','By Cargo')],
                                "Shipping Mode")
    deal = fields.Many2one('crm.lead',domain=[('type','=','opportunity')])

    order_id = fields.Many2one("sale.order", string="Order",compute="_compute_order_id", store=True)
    responsible_person = fields.Char(string='Contact Person')

    @api.depends('invoice_origin')
    def _compute_order_id(self):
        for rec in self:
            sale_id = self.env['sale.order'].sudo().search([('name','=',rec.invoice_origin)])
            rec.order_id = sale_id.id

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Account, self).create(vals_list)
        type_of_company = self.env['vx.type.of.company'].sudo().search([('is_existing_customer', '=', True)], limit=1)
        for rec in res:
            if type_of_company:
                rec.partner_id.write({'type_of_company': type_of_company.id})
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        # if product.partner_ref:
        #     values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            if product.description_sale:
                values.append(product.description_sale)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)


                                                



