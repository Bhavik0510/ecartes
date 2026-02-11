# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Advance_tax(models.Model):
    _name = 'advance.tax'
    _description = "Advancd Tax"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    state_name = fields.Char(string='Place of Supply')
    rate = fields.Float(string='Rate')
    gross_advance_receipt = fields.Float(string='Gross Receipt')
    cess_amount = fields.Float(string='Cess Amount')
