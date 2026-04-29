# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_invoice_target = fields.Boolean(
        string="Is Invoice Target",
        help="Mark this company as the receiver for mirrored invoices."
    )

    is_payment_target = fields.Boolean(
        string="Is Payment Target",
        help="Mark this company as the receiver for mirrored Payments."
    )
