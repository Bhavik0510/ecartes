# -*- coding: utf-8 -*-

from odoo import models , fields , api , _


class hsn_data(models.Model):
    _name = 'hsn.data'
    _description = "HSN Data"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    hsn_code = fields.Char(string='HSN')
    description = fields.Char(string='Description')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    total_quantity = fields.Float(string='Total Quantity')
    total_value = fields.Float(string='Total Value')
    taxable_value = fields.Float(string='Taxable Value')
    igst = fields.Float(string='Integrated Tax Amount')
    cgst = fields.Float(string='Central Tax Amount')
    sgst = fields.Float(string='State/UT Tax Amount')
    cess_amount = fields.Float(string='Cess Amount')
