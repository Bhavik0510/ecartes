# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class B2cs_Invoice(models.Model):
    _name = 'b2cs.invoice'
    _description = "B2CS Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    type = fields.Char(string='Type')
    state_name = fields.Char(string='Place of Supply')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
    cess_amount = fields.Float(string='Cess Amount')
    e_commerce_gstin = fields.Char(string='E-Comm GSTIN')
