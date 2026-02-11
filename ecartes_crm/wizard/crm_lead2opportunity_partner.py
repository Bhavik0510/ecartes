# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    lead_type = fields.Selection([('opportunity', 'Opportunity'), ('tender', 'Tender')],
        string="Pipeline Type", default='opportunity')

    def action_apply(self):
        if self.lead_type == 'opportunity':
            lead_id = self.env['crm.lead'].browse(self._context.get('active_ids', []))
            if lead_id:
                if not lead_id.street or not lead_id.city or not lead_id.zip or not lead_id.country_id:
                    raise UserError(_("Please Enter the address to convert lead to opportunity !"))
            return super(Lead2OpportunityPartner, self).action_apply()
        else:
            # print('------------tender--------')
            self.env["tender.pipeline"].create({'name': 'Test of tender Creation.'})
