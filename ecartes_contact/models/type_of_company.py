# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VXTypeofCompany(models.Model):
	_name = 'vx.type.of.company'
	_description = 'Type of Company'

	name = fields.Char(string='Name', required=True)
	description = fields.Text(string="Description")
	is_existing_customer = fields.Boolean(string="Is Existing Customer?")
