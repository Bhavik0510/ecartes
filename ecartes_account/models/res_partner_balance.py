# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartnerBalance(models.Model):
    _inherit = 'res.partner'

    partner_balance = fields.Monetary(
        string="Balance",
        compute="_compute_partner_balance",
        currency_field='currency_id',
    )

    def _compute_partner_balance(self):
        for partner in self:
            commercial = partner.commercial_partner_id or partner
            all_partners = self.env['res.partner'].search([
                '|', ('id', '=', commercial.id),
                ('id', 'child_of', commercial.id)
            ])

            # Total Receivable (debit balance on receivable accounts)
            receivable_lines = self.env['account.move.line'].sudo().search([
                ('partner_id', 'in', all_partners.ids),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
            ])
            total_receivable = sum(receivable_lines.mapped('debit')) - sum(receivable_lines.mapped('credit'))

            # Total Payable (credit balance on payable accounts)
            payable_lines = self.env['account.move.line'].sudo().search([
                ('partner_id', 'in', all_partners.ids),
                ('account_id.account_type', '=', 'liability_payable'),
                ('parent_state', '=', 'posted'),
            ])
            total_payable = sum(payable_lines.mapped('credit')) - sum(payable_lines.mapped('debit'))

            # Net balance: positive = they owe us, negative = we owe them
            partner.partner_balance = total_receivable - total_payable

    def action_view_partner_balance(self):
        """Open all journal entries for this partner."""
        self.ensure_one()
        commercial = self.commercial_partner_id or self
        all_partners = self.env['res.partner'].search([
            '|', ('id', '=', commercial.id),
            ('id', 'child_of', commercial.id)
        ])
        return {
            'name': f'Journal Entries - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [
                ('partner_id', 'in', all_partners.ids),
                ('state', '=', 'posted'),
            ],
            'context': {
                'default_partner_id': self.id,
            },
        }
