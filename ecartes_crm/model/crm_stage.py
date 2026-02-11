# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Stage(models.Model):
    _inherit = "crm.stage"

    is_tender_stage = fields.Boolean(string="Is Tender Stage?", default=False)
    is_qualified_stage = fields.Boolean(string="Is Qualified Stage?", default=False)
    is_financial_stage = fields.Boolean(string="Is Financial Stage?", default=False)
