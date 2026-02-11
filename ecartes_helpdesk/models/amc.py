# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Amc(models.Model):
    _inherit = 'amc.amc'

    amc_claim_ids = fields.One2many(comodel_name="helpdesk.ticket", inverse_name="amc_id", string="Claims History", tracking=True)
    claim_count = fields.Integer(compute='compute_claim_count')

    def compute_claim_count(self):
        for order in self:
            order.claim_count = self.env['helpdesk.ticket'].search_count([('amc_id', '=', self.id)])

    def get_amc(self):
        self.ensure_one()
        return {
            'name': _('Tickets'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('amc_id', '=', self.id)],
            'context': "{'create': False}"
        }   

    def create_amc_claim(self):
        if self.state == 'expired' and not self.env.user.has_group('ecartes_amc.allow_claim_forcefully'):
            raise ValidationError('Your amc is expired ')
        else:
            # self.write({'state': 'under_amc'})
            data = {
                'default_amc_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_amc_line_ids': [(6, 0, self.amc_line_ids.ids)],
            }
            return {
                'name': 'Tickets',
                'res_model': 'helpdesk.ticket',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                "context": data,
            }
