# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class docs_data(models.Model):
    _name = 'docs.data'
    _description = "Docs Data"

    gst_return_id = fields.Many2one('gstr.return', string='GST Return')
    nature_of_document = fields.Char(string='Nature of Document')
    no_from = fields.Char(string='No From')
    no_to = fields.Char(string='No To')
    total = fields.Integer(string='Total')
    cancelled = fields.Integer(string='Cancelled')
