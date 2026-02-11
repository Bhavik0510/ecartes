# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class B2cl_Invoice(models.Model):
    _name = 'b2cl.invoice'
    _description = "B2CL Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_date = fields.Date(string='Invoice Number')
    invoice_value = fields.Float(string='Invoice Value')
    state_name = fields.Char(string='Place of Supply')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
    cess_amount = fields.Float(string='Cess Amount')
    e_commerce_gstin = fields.Char(string='E-Comm GSTIN')
