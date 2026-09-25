# -*- coding: utf-8 -*-
from odoo import models, api, fields


def format_indian_amount(amount, show_zero=False):
    """Format amount using Indian numbering system (e.g. 1,91,363.30)."""
    if amount is None or amount == '':
        return '0.00' if show_zero else ''
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return ''
    if abs(amount) < 0.005:
        return '0.00' if show_zero else ''
    sign = '-' if amount < 0 else ''
    amount = abs(amount)
    integer, _, fraction = f'{amount:.2f}'.partition('.')
    if len(integer) <= 3:
        formatted_int = integer
    else:
        last3 = integer[-3:]
        rest = integer[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted_int = ','.join(parts) + ',' + last3
    return f'{sign}{formatted_int}.{fraction}'


class PartnerLedgerAbstract(models.AbstractModel):
    """
    Abstract model for generating partner ledger reports matching Tally statement format.
    """
    _name = 'report.tk_partner_ledger.report_partner_ledger_pdf'
    _description = 'Partner Ledger Pdf Report'

    def _get_line_particulars(self, line):
        """
        Determine the contra account particulars and prefix (Dr/Cr) for a partner move line.
        Rule:
        - If amount is in Credit column (partner was credited): prefix is 'Dr' (counterpart was debited).
        - If amount is in Debit column (partner was debited): prefix is 'Cr' (counterpart was credited).
        """
        move = line.move_id
        is_credit = (line.credit > 0)
        prefix = 'Dr' if is_credit else 'Cr'

        counterpart_name = ''

        # 1. Payment check: bank/cash journal or liquidity account
        payment = line.payment_id or getattr(move, 'origin_payment_id', False)
        if payment:
            counterpart_name = payment.journal_id.name or ''
            if not counterpart_name:
                other_lines = move.line_ids.filtered(lambda l: l.id != line.id and l.display_type not in ('line_section', 'line_note'))
                liquidity_lines = other_lines.filtered(
                    lambda l: l.account_id.account_type in ('asset_cash', 'bank') or l.journal_id.type in ('bank', 'cash')
                )
                if liquidity_lines:
                    counterpart_name = liquidity_lines[0].account_id.name

        # 2. Invoice / Vendor Bill check: expense or income accounts from invoice lines
        if not counterpart_name and move.is_invoice():
            inv_lines = move.invoice_line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note') and l.account_id)
            if inv_lines:
                acc_amounts = {}
                for il in inv_lines:
                    acc_name = il.account_id.name
                    if acc_name:
                        val = abs(getattr(il, 'price_subtotal', 0.0)) or abs(il.debit or il.credit)
                        acc_amounts[acc_name] = acc_amounts.get(acc_name, 0.0) + val
                sorted_accs = sorted(acc_amounts.keys(), key=lambda k: acc_amounts[k], reverse=True)
                if sorted_accs:
                    counterpart_name = sorted_accs[0]

        # 3. Journal Entry / generic contra lines: find contra lines on opposite side
        if not counterpart_name:
            other_lines = move.line_ids.filtered(lambda l: l.id != line.id and l.display_type not in ('line_section', 'line_note'))
            if is_credit:
                # Partner is credit -> contra is debit
                contra = other_lines.filtered(lambda l: l.debit > 0 and not l.tax_line_id)
                if not contra:
                    contra = other_lines.filtered(lambda l: l.debit > 0)
                if contra:
                    sorted_contra = sorted(contra, key=lambda l: l.debit, reverse=True)
                    counterpart_name = sorted_contra[0].account_id.name
            else:
                # Partner is debit -> contra is credit
                contra = other_lines.filtered(lambda l: l.credit > 0 and not l.tax_line_id)
                if not contra:
                    contra = other_lines.filtered(lambda l: l.credit > 0)
                if contra:
                    sorted_contra = sorted(contra, key=lambda l: l.credit, reverse=True)
                    counterpart_name = sorted_contra[0].account_id.name

        # 4. Fallback to move name or reference
        if not counterpart_name:
            counterpart_name = move.name or line.name or move.ref or 'General Ledger'

        return f"{prefix} {counterpart_name}"

    @api.model
    def _get_report_values(self, docids, data=None):
        if data and data.get('partner_id'):
            partner = self.env['res.partner'].browse(data.get('partner_id'))
            start_date = data.get('form_data', {}).get('start_date')
            end_date = data.get('form_data', {}).get('end_date')
            wizard = self.env['partner.ledger.report'].browse(docids) if docids else None
        elif docids:
            wizard = self.env['partner.ledger.report'].browse(docids)[0]
            partner = wizard.partner_id
            start_date = wizard.start_date
            end_date = wizard.end_date
        else:
            partner = self.env['res.partner']
            start_date = fields.Date.today()
            end_date = fields.Date.today()
            wizard = None

        if isinstance(start_date, str):
            start_date = fields.Date.from_string(start_date)
        if isinstance(end_date, str):
            end_date = fields.Date.from_string(end_date)
        if not start_date:
            start_date = fields.Date.today()
        if not end_date:
            end_date = fields.Date.today()

        company = self.env.company
        company_currency_symbol = company.currency_id.symbol

        # Company Header Lines
        company_address_lines = []
        if company.street:
            company_address_lines.append(company.street.rstrip(', '))
        if company.street2:
            company_address_lines.append(company.street2.rstrip(', '))
        city_parts = []
        if company.city:
            city_parts.append(company.city)
        if company.state_id:
            st = company.state_id.name
            if not any(st.lower() in p.lower() for p in city_parts):
                city_parts.append(st)
        city_line = ', '.join(city_parts)
        if company.zip:
            city_line = f"{city_line}-{company.zip}" if city_line else company.zip
        if city_line:
            company_address_lines.append(city_line)

        company_cin = company.company_registry or ''

        # Partner Header Lines
        partner_address_lines = []
        if partner.street:
            partner_address_lines.append(partner.street.rstrip(', '))
        if partner.street2:
            partner_address_lines.append(partner.street2.rstrip(', '))
        p_city_parts = []
        if partner.city:
            p_city_parts.append(partner.city)
        if partner.state_id:
            pst = partner.state_id.name
            if not any(pst.lower() in p.lower() for p in p_city_parts):
                p_city_parts.append(pst)
        p_city_line = ', '.join(p_city_parts)
        if partner.zip:
            p_city_line = f"{p_city_line}-{partner.zip}" if p_city_line else partner.zip
        if p_city_line:
            partner_address_lines.append(p_city_line)

        # Period label (e.g. 1-Apr-26 to 25-Sep-26)
        s_date_str = f"{start_date.day}-{start_date.strftime('%b')}-{start_date.strftime('%y')}"
        e_date_str = f"{end_date.day}-{end_date.strftime('%b')}-{end_date.strftime('%y')}"
        period_label = f"{s_date_str} to {e_date_str}"

        commercial_partner = partner.commercial_partner_id or partner
        all_partners = self.env['res.partner'].search([
            '|', ('id', '=', commercial_partner.id),
            ('id', 'child_of', commercial_partner.id)
        ])

        # ---------------------------------------------
        # Opening Balance (transactions before start_date)
        # ---------------------------------------------
        initial_lines = self.env['account.move.line'].search([
            ('partner_id', 'in', all_partners.ids),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('parent_state', '=', 'posted'),
            ('date', '<', start_date),
            '|', ('company_id', '=', company.id), ('company_id', '=', False),
        ])
        init_debit = sum(initial_lines.mapped('debit'))
        init_credit = sum(initial_lines.mapped('credit'))
        init_balance = init_debit - init_credit

        if init_balance < 0:
            # Credit balance (typical for vendor payable)
            opening_debit = 0.0
            opening_credit = abs(init_balance)
            opening_particulars = 'Dr Opening Balance'
        elif init_balance > 0:
            # Debit balance (typical for customer receivable)
            opening_debit = init_balance
            opening_credit = 0.0
            opening_particulars = 'Cr Opening Balance'
        else:
            opening_debit = 0.0
            opening_credit = 0.0
            opening_particulars = 'Dr Opening Balance'

        # ---------------------------------------------
        # Period Transactions (start_date to end_date)
        # ---------------------------------------------
        period_lines = self.env['account.move.line'].search([
            ('partner_id', 'in', all_partners.ids),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('parent_state', '=', 'posted'),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            '|', ('company_id', '=', company.id), ('company_id', '=', False),
        ], order='date asc, id asc')

        lines = []
        total_debit = 0.0
        total_credit = 0.0

        invoice_items = []
        payment_items = []

        for line in period_lines:
            if line.debit == 0 and line.credit == 0:
                continue

            ldebit = line.debit
            lcredit = line.credit
            total_debit += ldebit
            total_credit += lcredit

            d = line.date
            date_formatted = f"{d.day}-{d.strftime('%b')}-{d.strftime('%y')}" if d else ""

            move = line.move_id
            payment = line.payment_id or getattr(move, 'origin_payment_id', False)

            # Voucher Type
            if payment:
                if payment.payment_type == 'outbound':
                    vch_type = 'Payment'
                elif payment.payment_type == 'inbound':
                    vch_type = 'Receipt'
                else:
                    vch_type = line.journal_id.name or 'Payment'
            elif move.move_type in ('in_invoice', 'in_refund'):
                vch_type = line.journal_id.name or 'GST Purchase'
            elif move.move_type in ('out_invoice', 'out_refund'):
                vch_type = line.journal_id.name or 'Sales'
            else:
                vch_type = line.journal_id.name or 'Journal'

            # Voucher Number
            if move.move_type in ('in_invoice', 'in_refund'):
                vch_no = move.ref or move.name or ''
            elif move.move_type in ('out_invoice', 'out_refund'):
                vch_no = move.name or move.ref or ''
            elif payment:
                vch_no = payment.ref or move.ref or payment.name or move.name or ''
            else:
                vch_no = move.name or move.ref or ''

            particulars = self._get_line_particulars(line)

            lines.append({
                'date': line.date,
                'date_formatted': date_formatted,
                'display_date': date_formatted,
                'particulars': particulars,
                'vch_type': vch_type,
                'vch_no': vch_no,
                'debit': ldebit,
                'credit': lcredit,
                'debit_formatted': format_indian_amount(ldebit),
                'credit_formatted': format_indian_amount(lcredit),
            })

            # For backwards compatibility with legacy tests
            is_payable = (line.account_id.account_type == 'liability_payable')
            is_invoice = (line.credit > 0) if is_payable else (line.debit > 0)
            if is_invoice:
                amount = line.credit if is_payable else line.debit
                name = move.name or line.name or ''
                date_val = move.invoice_date or line.date
                invoice_items.append({'name': name, 'date': date_val, 'amount': amount})
            else:
                amount = line.debit if is_payable else line.credit
                name = move.name or (payment and payment.name) or line.name or ''
                date_val = line.date
                payment_items.append({'name': name, 'date': date_val, 'amount': amount})

        # Suppress duplicate date display on subsequent lines
        prev_date = None
        for l in lines:
            if l['date_formatted'] == prev_date:
                l['display_date'] = ''
            else:
                prev_date = l['date_formatted']

        # Subtotals (Opening + period transactions)
        subtotal_debit = opening_debit + total_debit
        subtotal_credit = opening_credit + total_credit

        # Closing balance balancing figure
        closing_diff = subtotal_credit - subtotal_debit
        if closing_diff > 0:
            closing_debit = closing_diff
            closing_credit = 0.0
            closing_particulars = 'Cr Closing Balance'
        elif closing_diff < 0:
            closing_debit = 0.0
            closing_credit = abs(closing_diff)
            closing_particulars = 'Dr Closing Balance'
        else:
            closing_debit = 0.0
            closing_credit = 0.0
            closing_particulars = 'Cr Closing Balance'

        grand_total_debit = subtotal_debit + closing_debit
        grand_total_credit = subtotal_credit + closing_credit

        combined_data = []
        for inv, pay in zip(invoice_items, payment_items):
            combined_data.append({
                'invoice_name': inv['name'], 'invoice_date': inv['date'], 'invoice_amount': inv['amount'],
                'payment_name': pay['name'], 'payment_date': pay['date'], 'payment_amount': pay['amount'],
            })
        if len(invoice_items) > len(payment_items):
            for inv in invoice_items[len(payment_items):]:
                combined_data.append({
                    'invoice_name': inv['name'], 'invoice_date': inv['date'], 'invoice_amount': inv['amount'],
                    'payment_name': '', 'payment_date': '', 'payment_amount': 0.0,
                })
        if len(payment_items) > len(invoice_items):
            for pay in payment_items[len(invoice_items):]:
                combined_data.append({
                    'invoice_name': '', 'invoice_date': '', 'invoice_amount': 0.0,
                    'payment_name': pay['name'], 'payment_date': pay['date'], 'payment_amount': pay['amount'],
                })

        return {
            'doc_ids': docids,
            'doc_model': 'partner.ledger.report',
            'docs': wizard or self.env['partner.ledger.report'].browse(docids),
            'company': company,
            'company_address_lines': company_address_lines,
            'company_cin': company_cin,
            'partner': partner,
            'partner_id': partner,
            'partner_address_lines': partner_address_lines,
            'period_label': period_label,
            'opening_date': s_date_str,
            'opening_particulars': opening_particulars,
            'opening_debit': opening_debit,
            'opening_credit': opening_credit,
            'opening_debit_formatted': format_indian_amount(opening_debit) if opening_debit else '',
            'opening_credit_formatted': format_indian_amount(opening_credit) if opening_credit else ('0.00' if not opening_debit else ''),
            'lines': lines,
            'subtotal_debit_formatted': format_indian_amount(subtotal_debit, show_zero=True),
            'subtotal_credit_formatted': format_indian_amount(subtotal_credit, show_zero=True),
            'closing_particulars': closing_particulars,
            'closing_debit': closing_debit,
            'closing_credit': closing_credit,
            'closing_debit_formatted': format_indian_amount(closing_debit) if closing_debit else '',
            'closing_credit_formatted': format_indian_amount(closing_credit) if closing_credit else '',
            'grand_total_debit_formatted': format_indian_amount(grand_total_debit, show_zero=True),
            'grand_total_credit_formatted': format_indian_amount(grand_total_credit, show_zero=True),
            'combined_data': combined_data,
            'payments': payment_items,
            'invoices': invoice_items,
            'currency': company_currency_symbol,
            'from_date': start_date,
            'to_date': end_date,
        }