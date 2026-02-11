# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class exempt_data(models.Model):
    _name = 'exempt.data'
    _description = "Exempt Data"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    description = fields.Char(string='Description')
    nil_rated_supplies = fields.Float(string='Nil Rated Supplies')
    exempt_supplies = fields.Float(string='Exempt Supplies')
    non_gst_supplies = fields.Float(string='Non GST Supplies')
    supply_type =  fields.Char(string='Supply Type')
