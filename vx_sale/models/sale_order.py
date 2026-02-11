# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            if not order.client_order_ref:
                raise ValidationError(_("Please Enter Customer Reference before confirm the order."))

        return super(SaleOrder, self).action_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('vx_sale.group_access_readonly_so'):
            raise ValidationError(_("You can't Create Sales Order/Quotation, Please Contact Your Administrator or Manager."))
        return super(SaleOrder, self).create(vals_list)
