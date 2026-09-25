# -*- coding: utf-8 -*-
from odoo import models, fields


class PartnerBalanceWizard(models.TransientModel):
    _name = 'partner.balance.wizard'
    _description = 'Partner Balance Details'

    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    total_receivable = fields.Monetary(
        string="Total Receivable",
        currency_field='currency_id',
        readonly=True,
    )
    total_payable = fields.Monetary(
        string="Total Payable",
        currency_field='currency_id',
        readonly=True,
    )
    net_balance = fields.Monetary(
        string="Net Balance",
        currency_field='currency_id',
        readonly=True,
    )

    def _get_partner_ids(self):
        """Get all child partner IDs for the commercial partner."""
        commercial = self.partner_id.commercial_partner_id or self.partner_id
        all_partners = self.env['res.partner'].search([
            '|', ('id', '=', commercial.id),
            ('id', 'child_of', commercial.id)
        ])
        return all_partners.ids

    def action_open_receivable_entries(self):
        """Open journal entries for receivable accounts."""
        self.ensure_one()
        partner_ids = self._get_partner_ids()
        return {
            'name': f'Receivable - {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', partner_ids),
                ('account_id.account_type', '=', 'asset_receivable'),
                ('parent_state', '=', 'posted'),
            ],
            'context': {'search_default_group_by_move': 1},
        }

    def action_open_payable_entries(self):
        """Open journal entries for payable accounts."""
        self.ensure_one()
        partner_ids = self._get_partner_ids()
        return {
            'name': f'Payable - {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', partner_ids),
                ('account_id.account_type', '=', 'liability_payable'),
                ('parent_state', '=', 'posted'),
            ],
            'context': {'search_default_group_by_move': 1},
        }

    def action_open_all_entries(self):
        """Open all journal entries (receivable + payable)."""
        self.ensure_one()
        partner_ids = self._get_partner_ids()
        return {
            'name': f'All Entries - {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'in', partner_ids),
                ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
                ('parent_state', '=', 'posted'),
            ],
            'context': {'search_default_group_by_move': 1},
        }
