import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        type_of_company = self.env['vx.type.of.company'].sudo().search([('is_existing_customer', '=', True)], limit=1)
        for rec in sale_orders:
            rec.partner_id.write({'type_of_company': type_of_company.id})
        return res
        