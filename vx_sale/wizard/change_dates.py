# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChangeDate(models.TransientModel):
    _name = "change.date"
    _description = "Change Date"

    order_date = fields.Date(string="Order Date", required=True)

    def action_update_date(self):
        active_id = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        order = self.env[active_model].browse(active_id)
        if active_model == 'sale.order':
            order.write({'date_order': self.order_date})
        # elif active_model == 'account.move':
        #     print('........invoice---date')
        elif active_model == 'purchase.order':
            order.write({'date_planned': self.order_date})
        # order.save()
