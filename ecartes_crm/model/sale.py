# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tender_pipeline_id = fields.Many2one(
        'tender.pipeline', string='Tender Pipeline', check_company=True,
        # readonly=True,
        # domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        domain="['&', '|', ('company_id', '=', False), ('company_id', '=', company_id), '|', ('stage_id.is_won', '=', True), ('stage_id.name', 'ilike', 'won')]")

