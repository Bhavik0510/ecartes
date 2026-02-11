# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def default_get(self, fields):
        if self.env.context.get('default_tp_id'):
            self = self.with_context(
                default_res_model_id=self.env.ref('ecartes_crm.model_tender_pipeline').id,
                default_res_id=self.env.context['default_tp_id']
            )
        defaults = super(CalendarEvent, self).default_get(fields)
        return defaults

    tp_id = fields.Many2one('tender.pipeline', 'Tender Pipeline', index=True, ondelete='set null')
