# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class tax_adjustment(models.Model):
    _name = 'tax.adjustment'
    _description = "Tax Adjustment"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    state_name = fields.Char(string='Place of Supply')
    rate = fields.Float(string='Rate')
    gross_advance_receipt = fields.Char(string='Gross advance Adjustment')
    cess_amount = fields.Float(string='Cess Amount')
