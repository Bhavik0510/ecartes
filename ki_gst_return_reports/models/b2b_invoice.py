# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class B2b_Invoice(models.Model):
    _name = 'b2b.invoice'
    _description = "B2B Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    gstin_number = fields.Char(string='GSTIN/UIN')
    invoice_id = fields.Many2one('account.move', string='Invoice Number')
    invoice_date = fields.Date(string='Invoice Date')
    invoice_value = fields.Float(string='Invoice Value')
    state_name = fields.Char(string='Place of Supply')
    reverse_charge = fields.Char(string='Reverse Charge')
    invoice_type = fields.Char(string='Invoice Type')
    e_commerce_gstin = fields.Char(string='E-Comm GSTIN')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
    cess_amount = fields.Float(string='Cess Amount')
