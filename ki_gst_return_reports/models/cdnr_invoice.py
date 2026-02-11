# -*- coding: utf-8 -*-
from odoo import models , fields , api , _


class Cdnr_Invoice(models.Model):
    _name = 'cdnr.invoice'
    _description = "CDNR Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    gstin_number = fields.Char(string='GSTIN/UIN')
    invoice_number = fields.Char(string='Invoice Number')
    invoice_date = fields.Char(string='Note / Voucher Date')
    voucher_id = fields.Many2one('account.move', string='Voucher Number')
    voucher_date = fields.Char(string='Notes / Voucher Date')
    document_type = fields.Char(string='Document Type')
    reason = fields.Char(string='Reason')
    state_name = fields.Char(string='Place of Supply')
    voucher_value = fields.Float(string='Voucher Value')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
    cess_amount = fields.Float(string='Cess Amount')
    pre_gst = fields.Char(string='Pre GST')
