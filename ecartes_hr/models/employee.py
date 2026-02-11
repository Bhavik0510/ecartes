# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class EcartesEmployee(models.Model):
    _inherit = 'hr.employee'

    p_o_box = fields.Char(string="P.O.Box")
    extension_num = fields.Char(string="Extension Number")
    website = fields.Char(string='Website')
    skype_name = fields.Char('Skype Name')
    twitter = fields.Char('Twitter')

class EcartesEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    p_o_box = fields.Char(string="P.O.Box")
    extension_num = fields.Char(string="Extension Number")
    website = fields.Char(string='Website')
    skype_name = fields.Char('Skype Name')
    twitter = fields.Char('Twitter')