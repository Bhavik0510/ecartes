# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_purchase = fields.Text(
        string="Remarks for Purchase", related="purchase_id.remarks")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks for Purchase")

    def write(self, vals):
        for rec in self:
            if rec.purchase_id and 'date_done' in vals and rec.company_id.backdate_for_stock_move:
                vals['date_done'] = rec.purchase_id.date_approve

            return super().write(vals)

    def _set_scheduled_date(self):
        for picking in self:
            picking.move_ids.write({'date': picking.scheduled_date})
