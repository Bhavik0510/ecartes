# -*- coding: utf-8 -*-
import base64
import logging
from datetime import date
from dateutil.relativedelta import relativedelta

try:
    import xlrd
except ImportError:
    xlrd = None

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class GstrDynamicReport(models.TransientModel):
    _name = 'gstr.dynamic.report'
    _description = 'Dynamic GSTR Report'

    @api.model
    def export_xlsx(self, report_type, date_from, date_to):
        """Invoke existing texbyte_gstr generators and return the download action."""
        model_map = {
            'gstr1': 'texbyte_gstr.report.gstr1',
            'gstr2': 'texbyte_gstr.report.gstr2',
            'gstr3b': 'texbyte_gstr.report.gstr3b',
            'gstr9': 'texbyte_gstr.report.gstr9',
        }
        method_map = {
            'gstr1': 'generate_gstr1_report',
            'gstr2': 'generate_gstr2_report',
            'gstr3b': 'generate_gstr3b_report',
            'gstr9': 'generate_gstr9_report',
        }
        model_name = model_map.get(report_type)
        method_name = method_map.get(report_type)
        if not model_name or not method_name:
            return False

        report_rec = self.env[model_name].create({
            'date_from': date_from,
            'date_to': date_to,
        })
        method = getattr(report_rec, method_name, None)
        if method:
            return method()
        return False

    @api.model
    def export_pdf(self, report_type, date_from, date_to):
        """Invoke report action to generate PDF matching the Excel data."""
        title_map = {
            'gstr1': 'GSTR-1 Report (Outward Supplies)',
            'gstr2': 'GSTR-2 Report (Inward Supplies)',
            'gstr3b': 'GSTR-3B Report (Monthly Return)',
            'gstr9': 'GSTR-9 Report (Annual Return)',
        }
        report_title = title_map.get(report_type, 'GSTR Report')
        data = {
            'report_type': report_type,
            'report_name': report_title,
            'date_from': str(date_from or ''),
            'date_to': str(date_to or ''),
        }
        return self.env.ref('arclight_account_custom.action_print_gstr_dynamic_report').report_action(
            self, data=data
        )

    @api.model
    def get_excel_tables(self, report_type, date_from, date_to):
        """Generate the Excel report using texbyte_gstr and parse all sheets into structured tables."""
        if not xlrd:
            _logger.warning("xlrd library is not available to parse Excel reports.")
            return []

        model_map = {
            'gstr1': 'texbyte_gstr.report.gstr1',
            'gstr2': 'texbyte_gstr.report.gstr2',
            'gstr3b': 'texbyte_gstr.report.gstr3b',
            'gstr9': 'texbyte_gstr.report.gstr9',
        }
        method_map = {
            'gstr1': 'generate_gstr1_report',
            'gstr2': 'generate_gstr2_report',
            'gstr3b': 'generate_gstr3b_report',
            'gstr9': 'generate_gstr9_report',
        }
        model_name = model_map.get(report_type)
        method_name = method_map.get(report_type)
        if not model_name or not method_name:
            return []

        try:
            report_rec = self.env[model_name].create({
                'date_from': date_from,
                'date_to': date_to,
            })
            method = getattr(report_rec, method_name, None)
            if not method:
                return []
            method()

            if not report_rec.report:
                return []

            xls_bytes = base64.b64decode(report_rec.report)
            workbook = xlrd.open_workbook(file_contents=xls_bytes)

            all_tables = []
            for sheet in workbook.sheets():
                tables = self._parse_sheet_to_tables(sheet, report_type)
                all_tables.extend(tables)

            # Cleanup transient record
            try:
                report_rec.unlink()
            except Exception:
                pass

            return all_tables
        except Exception as e:
            _logger.error("Failed to parse Excel report tables for %s: %s", report_type, e, exc_info=True)
            return []

    def _raw_cell_val(self, cell):
        if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
            return ""
        if cell.ctype == xlrd.XL_CELL_NUMBER:
            return cell.value
        if cell.ctype == xlrd.XL_CELL_TEXT:
            return cell.value.strip()
        if cell.ctype == xlrd.XL_CELL_BOOLEAN:
            return "Y" if cell.value else "N"
        if cell.ctype == xlrd.XL_CELL_DATE:
            try:
                dt_tuple = xlrd.xldate_as_tuple(cell.value, 0)
                return f"{dt_tuple[2]:02d}-{dt_tuple[1]:02d}-{dt_tuple[0]}"
            except Exception:
                return str(cell.value)
        return str(cell.value or "").strip()

    def _format_value_by_header(self, val, header=""):
        if val is None or val == "":
            return ""
        hdr_lower = str(header).lower()
        is_money = any(k in hdr_lower for k in [
            'val', 'tax', 'amt', 'amount', 'igst', 'cgst', 'sgst', 'cess', 'price', 'total'
        ]) and not any(k in hdr_lower for k in ['rate', 'count', 'no.', 'number', 'qty', 'quantity'])

        is_rate = 'rate' in hdr_lower or '%' in hdr_lower

        if isinstance(val, (int, float)):
            if is_money:
                return f"{val:,.2f}"
            if is_rate:
                return f"{int(val)}%" if val == int(val) else f"{val:,.2f}%"
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            if isinstance(val, float):
                return f"{val:,.2f}"
            return str(val)
        return str(val).strip()

    def _get_friendly_sheet_name(self, report_type, sheet_name):
        titles = {
            'b2b': 'B2B Invoices - 4A, 4B, 4C, 6B, 6C',
            'b2ba': 'B2B Amendments - 5A',
            'b2cl': 'B2CL (Large) Invoices - 5A, 5B',
            'b2cla': 'B2CL Amendments - 5B',
            'b2cs': 'B2CS (Small) Invoices - 7',
            'b2csa': 'B2CS Amendments - 7',
            'cdnr': 'Credit / Debit Notes (Registered) - 9B',
            'cdnra': 'Credit / Debit Notes (Registered) Amendments',
            'cdnur': 'Credit / Debit Notes (Unregistered) - 9B',
            'cdnura': 'Credit / Debit Notes (Unregistered) Amendments',
            'exp': 'Export Invoices - 6A',
            'expa': 'Export Amendments - 6A',
            'at': 'Tax on Advance - 11A',
            'ata': 'Amended Tax on Advance - 11A',
            'atadj': 'Advance Adjustments - 11B',
            'atadja': 'Amended Advance Adjustments - 11B',
            'exemp': 'Nil Rated / Exempted Supplies - 8',
            'hsn': 'HSN Wise Summary of Outward Supplies - 12',
            'hsn.b2b': 'HSN Summary (B2B)',
            'hsn.b2c': 'HSN Summary (B2C)',
            'docs': 'Summary of Documents Issued - 13',
            'b2bur': 'Inward Supplies from Unregistered Persons - 4A',
            'imps': 'Import of Services - 4B',
            'impg': 'Import of Goods - 5',
            'exempted': 'Nil Rated / Exempted Inward Supplies - 7',
            'itcr': 'ITC Reversals / Adjustments - 11',
            'gstr-3b': 'GSTR-3B Return Summary',
            '4.outward': '4. Details of Outward Supplies (Tax Payable)',
            '5 outward': '5. Details of Outward Supplies (Tax Not Payable)',
            '5.outward': '5. Details of Outward Supplies (Tax Not Payable)',
            '6.itc availed': '6. Details of ITC Availed during Financial Year',
            '17.hsn_out': '17. HSN Summary of Outward Supplies',
            '18.hsn_in': '18. HSN Summary of Inward Supplies',
        }
        key = (sheet_name or '').lower().strip()
        return titles.get(key, sheet_name.upper())

    def _parse_sheet_to_tables(self, sheet, report_type):
        if sheet.nrows == 0:
            return []

        all_rows = []
        for r in range(sheet.nrows):
            row_vals = [self._raw_cell_val(sheet.cell(r, c)) for c in range(sheet.ncols)]
            if any(v != "" for v in row_vals):
                all_rows.append(row_vals)

        if not all_rows:
            return []

        tables = []
        current_title = ""
        current_headers = []
        current_rows = []

        def save_table():
            nonlocal current_title, current_headers, current_rows
            if current_rows and (current_headers or any(len(r) > 1 for r in current_rows)):
                formatted_rows = []
                for r in current_rows:
                    fmt_r = []
                    for c_idx, val in enumerate(r):
                        hdr = current_headers[c_idx] if c_idx < len(current_headers) else ""
                        fmt_r.append(self._format_value_by_header(val, hdr))
                    formatted_rows.append(fmt_r)

                max_cols = max(len(current_headers), max(len(r) for r in formatted_rows) if formatted_rows else 0)
                if len(current_headers) < max_cols:
                    current_headers += [f"Col {i+1}" for i in range(len(current_headers), max_cols)]
                for r in formatted_rows:
                    if len(r) < max_cols:
                        r += [""] * (max_cols - len(r))

                sheet_code = sheet.name.lower().strip()
                tables.append({
                    'sheet_code': sheet_code,
                    'title': current_title or self._get_friendly_sheet_name(report_type, sheet.name),
                    'headers': current_headers,
                    'rows': formatted_rows,
                    'row_count': len(formatted_rows),
                })
            current_title = ""
            current_headers = []
            current_rows = []

        i = 0
        while i < len(all_rows):
            row = all_rows[i]
            non_empty = [v for v in row if v != ""]
            if not non_empty:
                i += 1
                continue

            first_val_str = str(non_empty[0]).strip().lower()
            if len(non_empty) <= 2 and any(first_val_str.startswith(m) for m in ['from:', 'to:', 'gstin', 'legal name']):
                i += 1
                continue

            if len(non_empty) == 1:
                title_text = str(non_empty[0]).strip()
                if current_rows:
                    save_table()
                current_title = title_text
                i += 1
                continue

            has_only_strings = all(
                isinstance(v, str) and not v.replace('.', '', 1).replace('-', '', 1).isdigit()
                for v in non_empty
            )
            if not current_headers and has_only_strings:
                current_headers = [str(v).strip() for v in row]
                i += 1
                continue

            current_rows.append(row)
            i += 1

        if current_rows:
            save_table()

        return tables

    def _format_date_tally(self, d):
        if not d:
            return ""
        if isinstance(d, str):
            try:
                d = fields.Date.from_string(d)
            except Exception:
                return str(d)
        try:
            return d.strftime("%-d-%b-%y")
        except Exception:
            return d.strftime("%d-%b-%y").lstrip("0")

    @api.model
    def get_report_data(self, report_type, date_from, date_to):
        """Fetch summary data and Excel sheets for the requested GSTR report."""
        if not date_from:
            date_from = date.today().replace(day=1) - relativedelta(months=1)
        if not date_to:
            date_to = date.today().replace(day=1) - relativedelta(days=1)

        company = self.env.company

        if report_type == 'gstr1':
            res = self._get_gstr1_data(date_from, date_to, company)
        elif report_type == 'gstr2':
            res = self._get_gstr2_data(date_from, date_to, company)
        elif report_type == 'gstr3b':
            res = self._get_gstr3b_data(date_from, date_to, company)
        elif report_type == 'gstr9':
            res = self._get_gstr9_data(date_from, date_to, company)
        else:
            res = {'headers': [], 'sections': [], 'totals': {}}

        # Format dates for Tally header
        period_display = f"{self._format_date_tally(date_from)} to {self._format_date_tally(date_to)}"
        res.setdefault('company_gstin', company.vat or '')
        res.setdefault('company_name', company.name or '')
        res.setdefault('period_display', period_display)

        # Total vouchers count across company
        total_vouchers = self.env['account.move'].search_count([
            ('company_id', '=', company.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        doc_count = res.get('totals', {}).get('doc_count', 0)
        if total_vouchers < doc_count:
            total_vouchers = doc_count

        res.setdefault('vouchers_summary', {
            'total_vouchers': total_vouchers,
            'included_in_return': doc_count,
            'included_in_hsn': doc_count,
            'incomplete_hsn': 0,
            'not_relevant': max(0, total_vouchers - doc_count),
            'uncertain': 0,
        })

        # Fetch Excel detailed tables from texbyte_gstr
        try:
            res['tables'] = self.get_excel_tables(report_type, date_from, date_to)
        except Exception as e:
            _logger.error("Error fetching excel tables in get_report_data: %s", e)
            res['tables'] = []
        return res

    def _get_tax_breakup(self, move):
        """Calculate tax breakup (IGST, CGST, SGST, Cess) for a given account.move."""
        igst = 0.0
        cgst = 0.0
        sgst = 0.0
        cess = 0.0
        for line in move.line_ids.filtered(lambda l: l.tax_line_id):
            tax_name = (line.tax_line_id.name or '').upper()
            amt = abs(line.balance)
            if 'IGST' in tax_name:
                igst += amt
            elif 'CGST' in tax_name:
                cgst += amt
            elif 'SGST' in tax_name or 'UTGST' in tax_name:
                sgst += amt
            elif 'CESS' in tax_name:
                cess += amt
            else:
                igst += amt
        return igst, cgst, sgst, cess

    def _get_gstr1_data(self, date_from, date_to, company):
        headers = [
            {'name': 'Sl No.', 'align': 'center', 'width': '35px'},
            {'name': 'P a r t i c u l a r s', 'align': 'left'},
            {'name': 'Voucher Count', 'align': 'right'},
            {'name': 'Taxable Amount', 'align': 'right'},
            {'name': 'Integrated Tax Amount', 'align': 'right'},
            {'name': 'Central Tax Amount', 'align': 'right'},
            {'name': 'State Tax Amount', 'align': 'right'},
            {'name': 'Cess Amount', 'align': 'right'},
            {'name': 'Tax Amount', 'align': 'right'},
            {'name': 'Invoice Amount', 'align': 'right'},
        ]

        moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ])

        section_defs = [
            (1, 'B2B Invoices - 4A, 4B, 4C, 6B, 6C', 'b2b'),
            (2, 'B2C(Large) Invoices - 5A, 5B', 'b2cl'),
            (3, 'B2C(Small) Invoices - 7', 'b2cs'),
            (4, 'Credit/Debit Notes(Registered) - 9B', 'cdnr'),
            (5, 'Credit/Debit Notes(Unregistered) - 9B', 'cdnur'),
            (6, 'Exports Invoices - 6A', 'exp'),
            (7, 'Tax Liability(Advances received) - 11A(1), 11A(2)', 'at'),
            (8, 'Adjustment of Advances - 11B(1), 11B(2)', 'atadj'),
            (9, 'Nil Rated Invoices - 8A, 8B, 8C, 8D', 'exemp'),
        ]

        buckets = {key: {'count': 0, 'taxable': 0.0, 'igst': 0.0, 'cgst': 0.0, 'sgst': 0.0, 'cess': 0.0, 'total': 0.0} for _, _, key in section_defs}

        company_state = company.state_id

        for move in moves:
            partner = move.partner_id
            is_refund = move.move_type == 'out_refund'
            has_gstin = bool(partner.vat and len(partner.vat.strip()) == 15)
            is_inter_state = bool(partner.state_id and company_state and partner.state_id != company_state)
            is_export = bool(partner.country_id and partner.country_id != company.country_id)
            sign = -1.0 if is_refund else 1.0

            igst, cgst, sgst, cess = self._get_tax_breakup(move)
            taxable = move.amount_untaxed * sign
            total = move.amount_total * sign
            igst *= sign
            cgst *= sign
            sgst *= sign
            cess *= sign

            is_nil_or_exempt = False
            if not is_refund and not is_export:
                if abs(move.amount_tax) < 0.001 and abs(move.amount_untaxed) > 0:
                    is_nil_or_exempt = True

            if is_refund:
                cat = 'cdnr' if has_gstin else 'cdnur'
            elif is_export:
                cat = 'exp'
            elif is_nil_or_exempt:
                cat = 'exemp'
            elif has_gstin:
                cat = 'b2b'
            elif is_inter_state and abs(move.amount_total) > 100000:
                cat = 'b2cl'
            else:
                cat = 'b2cs'

            b = buckets[cat]
            b['count'] += 1
            b['taxable'] += taxable
            b['igst'] += igst
            b['cgst'] += cgst
            b['sgst'] += sgst
            b['cess'] += cess
            b['total'] += total

        sections = []
        tot_count = 0
        tot_taxable = 0.0
        tot_igst = 0.0
        tot_cgst = 0.0
        tot_sgst = 0.0
        tot_cess = 0.0
        tot_tax_amount = 0.0
        tot_invoice_amount = 0.0

        for sr_no, label, key in section_defs:
            b = buckets[key]
            tax_amt = round(b['igst'] + b['cgst'] + b['sgst'] + b['cess'], 2)
            inv_amt = round(b['taxable'] + tax_amt, 2)
            sections.append({
                'sr_no': sr_no,
                'section': label,
                'sheet_code': key,
                'doc_count': b['count'],
                'taxable_value': round(b['taxable'], 2),
                'igst': round(b['igst'], 2),
                'cgst': round(b['cgst'], 2),
                'sgst': round(b['sgst'], 2),
                'cess': round(b['cess'], 2),
                'tax_amount': tax_amt,
                'invoice_amount': inv_amt,
                'total_value': inv_amt,
            })
            tot_count += b['count']
            tot_taxable += b['taxable']
            tot_igst += b['igst']
            tot_cgst += b['cgst']
            tot_sgst += b['sgst']
            tot_cess += b['cess']
            tot_tax_amount += tax_amt
            tot_invoice_amount += inv_amt

        period_display = f"{self._format_date_tally(date_from)} to {self._format_date_tally(date_to)}"

        totals = {
            'doc_count': tot_count,
            'taxable_value': round(tot_taxable, 2),
            'igst': round(tot_igst, 2),
            'cgst': round(tot_cgst, 2),
            'sgst': round(tot_sgst, 2),
            'cess': round(tot_cess, 2),
            'tax_amount': round(tot_tax_amount, 2),
            'invoice_amount': round(tot_invoice_amount, 2),
            'total_value': round(tot_invoice_amount, 2),
        }

        return {
            'headers': headers,
            'sections': sections,
            'totals': totals,
            'company_gstin': company.vat or '',
            'period_display': period_display,
        }

    def _get_gstr2_data(self, date_from, date_to, company):
        headers = [
            {'name': 'Section / Nature of Inward Supply', 'align': 'left'},
            {'name': 'No. of Bills', 'align': 'right'},
            {'name': 'Taxable Value', 'align': 'right'},
            {'name': 'IGST', 'align': 'right'},
            {'name': 'CGST', 'align': 'right'},
            {'name': 'SGST', 'align': 'right'},
            {'name': 'Cess', 'align': 'right'},
            {'name': 'Total Value', 'align': 'right'},
        ]

        moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ])

        section_defs = [
            ('3 - Inward Supplies from Registered Taxpayers (B2B)', 'b2b'),
            ('4A - Inward Supplies from Unregistered Taxpayers (B2BUR)', 'b2bur'),
            ('4B - Import of Services (IMPS)', 'imps'),
            ('5 - Import of Goods (IMPG)', 'impg'),
            ('4C - Credit / Debit Notes for Registered Taxpayers (CDNR)', 'cdnr'),
            ('4D - Credit / Debit Notes for Unregistered Taxpayers (CDNUR)', 'cdnur'),
            ('13 - HSN Summary of Inward Supplies', 'hsn'),
        ]

        buckets = {key: {'count': 0, 'taxable': 0.0, 'igst': 0.0, 'cgst': 0.0, 'sgst': 0.0, 'cess': 0.0, 'total': 0.0} for _, key in section_defs}

        for move in moves:
            partner = move.partner_id
            is_refund = move.move_type == 'in_refund'
            has_gstin = bool(partner.vat and len(partner.vat.strip()) == 15)
            is_overseas = partner.country_id and partner.country_id != company.country_id
            sign = -1.0 if is_refund else 1.0

            igst, cgst, sgst, cess = self._get_tax_breakup(move)
            taxable = move.amount_untaxed * sign
            total = move.amount_total * sign
            igst *= sign
            cgst *= sign
            sgst *= sign
            cess *= sign

            if is_refund:
                cat = 'cdnr' if has_gstin else 'cdnur'
            elif is_overseas:
                cat = 'impg'
            elif has_gstin:
                cat = 'b2b'
            else:
                cat = 'b2bur'

            b = buckets[cat]
            b['count'] += 1
            b['taxable'] += taxable
            b['igst'] += igst
            b['cgst'] += cgst
            b['sgst'] += sgst
            b['cess'] += cess
            b['total'] += total

        sections = []
        tot_count = 0
        tot_taxable = 0.0
        tot_igst = 0.0
        tot_cgst = 0.0
        tot_sgst = 0.0
        tot_cess = 0.0
        tot_value = 0.0

        for label, key in section_defs:
            b = buckets[key]
            sections.append({
                'section': label,
                'doc_count': b['count'],
                'taxable_value': round(b['taxable'], 2),
                'igst': round(b['igst'], 2),
                'cgst': round(b['cgst'], 2),
                'sgst': round(b['sgst'], 2),
                'cess': round(b['cess'], 2),
                'total_value': round(b['total'], 2),
            })
            tot_count += b['count']
            tot_taxable += b['taxable']
            tot_igst += b['igst']
            tot_cgst += b['cgst']
            tot_sgst += b['sgst']
            tot_cess += b['cess']
            tot_value += b['total']

        return {
            'headers': headers,
            'sections': sections,
            'totals': {
                'doc_count': tot_count,
                'taxable_value': round(tot_taxable, 2),
                'igst': round(tot_igst, 2),
                'cgst': round(tot_cgst, 2),
                'sgst': round(tot_sgst, 2),
                'cess': round(tot_cess, 2),
                'total_value': round(tot_value, 2),
            }
        }

    def _get_gstr3b_data(self, date_from, date_to, company):
        headers = [
            {'name': 'Nature of Supplies / ITC Category', 'align': 'left'},
            {'name': 'Taxable Value', 'align': 'right'},
            {'name': 'Integrated Tax (IGST)', 'align': 'right'},
            {'name': 'Central Tax (CGST)', 'align': 'right'},
            {'name': 'State/UT Tax (SGST)', 'align': 'right'},
            {'name': 'Cess', 'align': 'right'},
            {'name': 'Total Tax', 'align': 'right'},
        ]

        out_moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ])

        in_moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ])

        # 3.1 Outward supplies totals
        out_taxable = sum(m.amount_untaxed * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)
        out_igst = 0.0
        out_cgst = 0.0
        out_sgst = 0.0
        out_cess = 0.0
        for m in out_moves:
            sign = -1.0 if m.move_type == 'out_refund' else 1.0
            i, c, s, cs = self._get_tax_breakup(m)
            out_igst += i * sign
            out_cgst += c * sign
            out_sgst += s * sign
            out_cess += cs * sign

        # 4. Eligible ITC totals
        itc_taxable = sum(m.amount_untaxed * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)
        itc_igst = 0.0
        itc_cgst = 0.0
        itc_sgst = 0.0
        itc_cess = 0.0
        for m in in_moves:
            sign = -1.0 if m.move_type == 'in_refund' else 1.0
            i, c, s, cs = self._get_tax_breakup(m)
            itc_igst += i * sign
            itc_cgst += c * sign
            itc_sgst += s * sign
            itc_cess += cs * sign

        sections = [
            {
                'section': '3.1(a) Outward Taxable Supplies (other than zero rated, nil rated, exempted)',
                'taxable_value': round(out_taxable, 2),
                'igst': round(out_igst, 2),
                'cgst': round(out_cgst, 2),
                'sgst': round(out_sgst, 2),
                'cess': round(out_cess, 2),
                'total_value': round(out_igst + out_cgst + out_sgst + out_cess, 2),
            },
            {
                'section': '3.1(b) Outward Taxable Supplies (zero rated / Export)',
                'taxable_value': 0.0,
                'igst': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'cess': 0.0,
                'total_value': 0.0,
            },
            {
                'section': '3.1(c) Other Outward Supplies (nil rated, exempted)',
                'taxable_value': 0.0,
                'igst': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'cess': 0.0,
                'total_value': 0.0,
            },
            {
                'section': '3.1(d) Inward Supplies (liable to reverse charge)',
                'taxable_value': 0.0,
                'igst': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'cess': 0.0,
                'total_value': 0.0,
            },
            {
                'section': '4(A) Eligible ITC - Inward Supplies from Registered Suppliers',
                'taxable_value': round(itc_taxable, 2),
                'igst': round(itc_igst, 2),
                'cgst': round(itc_cgst, 2),
                'sgst': round(itc_sgst, 2),
                'cess': round(itc_cess, 2),
                'total_value': round(itc_igst + itc_cgst + itc_sgst + itc_cess, 2),
            },
            {
                'section': '4(B) ITC Reversed / Ineligible',
                'taxable_value': 0.0,
                'igst': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'cess': 0.0,
                'total_value': 0.0,
            },
            {
                'section': '4(C) Net ITC Available (4A - 4B)',
                'taxable_value': round(itc_taxable, 2),
                'igst': round(itc_igst, 2),
                'cgst': round(itc_cgst, 2),
                'sgst': round(itc_sgst, 2),
                'cess': round(itc_cess, 2),
                'total_value': round(itc_igst + itc_cgst + itc_sgst + itc_cess, 2),
            },
        ]

        tot_taxable = out_taxable + itc_taxable
        tot_igst = out_igst + itc_igst
        tot_cgst = out_cgst + itc_cgst
        tot_sgst = out_sgst + itc_sgst
        tot_cess = out_cess + itc_cess

        return {
            'headers': headers,
            'sections': sections,
            'totals': {
                'taxable_value': round(tot_taxable, 2),
                'igst': round(tot_igst, 2),
                'cgst': round(tot_cgst, 2),
                'sgst': round(tot_sgst, 2),
                'cess': round(tot_cess, 2),
                'total_value': round(tot_igst + tot_cgst + tot_sgst + tot_cess, 2),
            }
        }

    def _get_gstr9_data(self, date_from, date_to, company):
        headers = [
            {'name': 'Description / Return Section', 'align': 'left'},
            {'name': 'Taxable Value', 'align': 'right'},
            {'name': 'IGST', 'align': 'right'},
            {'name': 'CGST', 'align': 'right'},
            {'name': 'SGST', 'align': 'right'},
            {'name': 'Cess', 'align': 'right'},
            {'name': 'Total Tax', 'align': 'right'},
        ]

        out_moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ])

        in_moves = self.env['account.move'].search([
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ])

        out_taxable = sum(m.amount_untaxed * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)
        out_igst = sum(self._get_tax_breakup(m)[0] * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)
        out_cgst = sum(self._get_tax_breakup(m)[1] * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)
        out_sgst = sum(self._get_tax_breakup(m)[2] * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)
        out_cess = sum(self._get_tax_breakup(m)[3] * (-1.0 if m.move_type == 'out_refund' else 1.0) for m in out_moves)

        itc_taxable = sum(m.amount_untaxed * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)
        itc_igst = sum(self._get_tax_breakup(m)[0] * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)
        itc_cgst = sum(self._get_tax_breakup(m)[1] * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)
        itc_sgst = sum(self._get_tax_breakup(m)[2] * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)
        itc_cess = sum(self._get_tax_breakup(m)[3] * (-1.0 if m.move_type == 'in_refund' else 1.0) for m in in_moves)

        sections = [
            {
                'section': '4. Details of Outward Supplies on which tax is payable',
                'taxable_value': round(out_taxable, 2),
                'igst': round(out_igst, 2),
                'cgst': round(out_cgst, 2),
                'sgst': round(out_sgst, 2),
                'cess': round(out_cess, 2),
                'total_value': round(out_igst + out_cgst + out_sgst + out_cess, 2),
            },
            {
                'section': '5. Details of Outward Supplies on which tax is not payable',
                'taxable_value': 0.0,
                'igst': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'cess': 0.0,
                'total_value': 0.0,
            },
            {
                'section': '6. Total ITC Availed during the financial year',
                'taxable_value': round(itc_taxable, 2),
                'igst': round(itc_igst, 2),
                'cgst': round(itc_cgst, 2),
                'sgst': round(itc_sgst, 2),
                'cess': round(itc_cess, 2),
                'total_value': round(itc_igst + itc_cgst + itc_sgst + itc_cess, 2),
            },
            {
                'section': '9. Details of Tax paid as declared in returns filed',
                'taxable_value': round(out_taxable, 2),
                'igst': round(out_igst, 2),
                'cgst': round(out_cgst, 2),
                'sgst': round(out_sgst, 2),
                'cess': round(out_cess, 2),
                'total_value': round(out_igst + out_cgst + out_sgst + out_cess, 2),
            },
            {
                'section': '17. HSN Summary of Outward Supplies',
                'taxable_value': round(out_taxable, 2),
                'igst': round(out_igst, 2),
                'cgst': round(out_cgst, 2),
                'sgst': round(out_sgst, 2),
                'cess': round(out_cess, 2),
                'total_value': round(out_igst + out_cgst + out_sgst + out_cess, 2),
            },
            {
                'section': '18. HSN Summary of Inward Supplies',
                'taxable_value': round(itc_taxable, 2),
                'igst': round(itc_igst, 2),
                'cgst': round(itc_cgst, 2),
                'sgst': round(itc_sgst, 2),
                'cess': round(itc_cess, 2),
                'total_value': round(itc_igst + itc_cgst + itc_sgst + itc_cess, 2),
            },
        ]

        tot_taxable = out_taxable
        tot_igst = out_igst
        tot_cgst = out_cgst
        tot_sgst = out_sgst
        tot_cess = out_cess

        return {
            'headers': headers,
            'sections': sections,
            'totals': {
                'taxable_value': round(tot_taxable, 2),
                'igst': round(tot_igst, 2),
                'cgst': round(tot_cgst, 2),
                'sgst': round(tot_sgst, 2),
                'cess': round(tot_cess, 2),
                'total_value': round(tot_igst + tot_cgst + tot_sgst + tot_cess, 2),
            }
        }


class GstrDynamicReportPdf(models.AbstractModel):
    _name = 'report.arclight_account_custom.gstr_dynamic_report_pdf'
    _description = 'GSTR Dynamic Report PDF'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        report_type = data.get('report_type', 'gstr1')
        date_from = data.get('date_from', '')
        date_to = data.get('date_to', '')
        report_name = data.get('report_name', 'GSTR Report')

        company = self.env.company
        report_obj = self.env['gstr.dynamic.report']

        # 1. Fetch Executive Summary Data
        summary = report_obj.get_report_data(report_type, date_from, date_to)
        sections = []
        for sec in summary.get('sections', []):
            s = dict(sec)
            for k in ['taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'tax_amount', 'invoice_amount', 'total_value']:
                val = sec.get(k, 0.0)
                if val and abs(val) >= 0.001:
                    is_neg = val < 0
                    formatted = f"{abs(val):,.2f}"
                    s[k + '_display'] = f"(-){formatted}" if is_neg else formatted
                else:
                    s[k + '_display'] = ""
            s['doc_count_display'] = str(sec.get('doc_count')) if sec.get('doc_count') else ""
            sections.append(s)

        totals = dict(summary.get('totals', {}))
        for k in ['taxable_value', 'igst', 'cgst', 'sgst', 'cess', 'tax_amount', 'invoice_amount', 'total_value']:
            val = totals.get(k, 0.0)
            if val and abs(val) >= 0.001:
                is_neg = val < 0
                formatted = f"{abs(val):,.2f}"
                totals[k + '_display'] = f"(-){formatted}" if is_neg else formatted
            else:
                totals[k + '_display'] = ""
        totals['doc_count_display'] = str(totals.get('doc_count')) if totals.get('doc_count') else ""

        # 2. Detailed Tables from the generated Excel report
        tables = summary.get('tables') or report_obj.get_excel_tables(report_type, date_from, date_to)

        return {
            'doc_ids': docids,
            'doc_model': 'gstr.dynamic.report',
            'company': company,
            'report_name': report_name,
            'report_type': report_type,
            'date_from': date_from,
            'date_to': date_to,
            'headers': summary.get('headers', []),
            'sections': sections,
            'totals': totals,
            'tables': tables,
            'company_gstin': summary.get('company_gstin', company.vat or ''),
            'period_display': summary.get('period_display', ''),
            'vouchers_summary': summary.get('vouchers_summary', {}),
        }

