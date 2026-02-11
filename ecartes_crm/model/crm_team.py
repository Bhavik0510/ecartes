# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Team(models.Model):
    _inherit = 'crm.team'

    is_tender_team = fields.Boolean(string="Is Tender Team?", default=False)
