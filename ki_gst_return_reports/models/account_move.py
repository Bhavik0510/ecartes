# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    e_commerce_gst = fields.Char(
        string="E-commerce GSTIN",
        size=15,
    )
    reversed_charged = fields.Selection(
        [('y', 'Yes'), ('n', 'No')],
        string="Reverse Charge(Y/N)",
        default="n"
    )






