# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Export_Invoice(models.Model):
    _name = 'export.invoice'
    _description = "Export Invoice"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    export_type = fields.Char(string='Export Type')
    invoice_id = fields.Many2one('account.move', string='Invoice Number')
    invoice_date = fields.Char(string='Invoice Date')
    invoice_value = fields.Float(string='Invoice Value')
    port_code = fields.Char(string='Port Code')
    shipping_bill_number = fields.Char(string='Shipping Bill Number')
    shipping_bill_date = fields.Date(string='Shipping Bill Date')
    rate = fields.Float(string='Rate')
    taxable_value = fields.Float(string='Taxable Value')
