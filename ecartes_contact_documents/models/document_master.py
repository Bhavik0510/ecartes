# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ContactDocumentstype(models.Model):
    _name = 'contact.document.master'
    _description = "Contact Documents"

    name = fields.Char(string='Document Name', copy=False, required=True)
