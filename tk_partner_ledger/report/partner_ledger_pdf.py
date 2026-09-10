# -*- coding: utf-8 -*-
from odoo import models, api


class PartnerLedgerAbstract(models.AbstractModel):
    """
        Abstract model for generating partner ledger reports.
    """
    _name = 'report.tk_partner_ledger.report_partner_ledger_pdf'
    _description = 'Partner Ledger Pdf Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        partner_id = data.get('partner_id')
        start_date = data.get('form_data', {}).get('start_date')
        end_date = data.get('form_data', {}).get('end_date')

        partner = self.env['res.partner'].browse(partner_id)  # ← browse to get recordset
        company_currency_symbol = self.env.user.company_id.currency_id.symbol

        commercial_partner = partner.commercial_partner_id or partner
        all_partners = self.env['res.partner'].search([
            '|', ('id', '=', commercial_partner.id),
            ('id', 'child_of', commercial_partner.id)
        ])

        move_lines = self.env['account.move.line'].search([
            ('partner_id', 'in', all_partners.ids),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('parent_state', '=', 'posted'),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ], order='date desc, id desc')

        invoice_items = []
        payment_items = []
        for line in move_lines:
            if line.debit == 0 and line.credit == 0:
                continue
            is_payable = (line.account_id.account_type == 'liability_payable')
            is_invoice = (line.credit > 0) if is_payable else (line.debit > 0)

            if is_invoice:
                amount = line.credit if is_payable else line.debit
                name = line.move_id.name or line.name or ''
                date_val = line.move_id.invoice_date or line.date
                invoice_items.append({
                    'name': name,
                    'date': date_val,
                    'amount': amount,
                })
            else:
                amount = line.debit if is_payable else line.credit
                name = line.move_id.name or line.payment_id.name or line.name or ''
                date_val = line.date
                payment_items.append({
                    'name': name,
                    'date': date_val,
                    'amount': amount,
                })

        combined_data = []
        for invoice, payment in zip(invoice_items, payment_items):
            combined_data.append({
                'invoice_name': invoice['name'],
                'invoice_date': invoice['date'],
                'invoice_amount': invoice['amount'],
                'payment_name': payment['name'],
                'payment_date': payment['date'],
                'payment_amount': payment['amount'],
            })
        if len(invoice_items) > len(payment_items):
            for invoice in invoice_items[len(payment_items):]:
                combined_data.append({
                    'invoice_name': invoice['name'],
                    'invoice_date': invoice['date'],
                    'invoice_amount': invoice['amount'],
                    'payment_name': '',
                    'payment_date': '',
                    'payment_amount': 0.0,
                })
        if len(payment_items) > len(invoice_items):
            for payment in payment_items[len(invoice_items):]:
                combined_data.append({
                    'invoice_name': '',
                    'invoice_date': '',
                    'invoice_amount': 0.0,
                    'payment_name': payment['name'],
                    'payment_date': payment['date'],
                    'payment_amount': payment['amount'],
                })

        return {
            'doc_ids': docids,
            'doc_model': 'partner.ledger.report',
            'docs': self.env['partner.ledger.report'].browse(docids),
            'combined_data': combined_data,
            'partner_id': partner,  # ← recordset, so partner_id.name / partner_id.email works in template
            'payments': payment_items,
            'invoices': invoice_items,
            'currency': company_currency_symbol,
            'from_date': start_date,
            'to_date': end_date,
        }