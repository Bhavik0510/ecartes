# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    remarks_for_purchase = fields.Text(string="Remarks for Purchase")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks for Purchase")
