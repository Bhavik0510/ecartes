# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Cdnur_Invoice(models.Model):
    _name = 'cdnur.invoice'
    _description = "CDNUR Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    ur_type = fields.Char(string='Ur Type')
    voucher_id = fields.Many2one('account.move', string='Note / Voucher Number')
    voucher_date = fields.Char(string='Note / Voucher Date')
    document_type = fields.Char(string='Document Type')
    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Char(string='Invoice Date')
    reason = fields.Char(string='Reason')
    state_name = fields.Char(string='Place of Supply')
    voucher_value = fields.Float(string='Voucher Value')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
    cess_amount = fields.Float(string='Cess Amount')
    pre_gst = fields.Char(string='Pre GST')
