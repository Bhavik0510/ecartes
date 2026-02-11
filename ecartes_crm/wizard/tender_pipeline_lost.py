# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.tools.mail import is_html_empty


class TenderPipelineLost(models.TransientModel):
    _name = 'tender.pipeline.lost'
    _description = 'Get Lost Reason for Tender'

    lost_reason = fields.Many2one('crm.lost.reason', 'Lost Reason')

    def action_lost_reason_apply(self):
        self.ensure_one()
        tenders = self.env['tender.pipeline'].browse(self.env.context.get('active_ids'))
        res = tenders.action_set_lost(lost_reason=self.lost_reason.id)
        return res
