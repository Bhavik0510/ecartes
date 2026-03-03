from datetime import date
from io import BytesIO

import base64
import xlwt
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class HsnSummaryReport(models.TransientModel):
    _name = 'arclight_account_custom.report.hsn_summary'
    _description = 'HSN Wise Summary Report'

    date_from = fields.Date(
        'Date From',
        default=lambda self: date.today().replace(day=1) - relativedelta(months=1),
    )
    date_to = fields.Date(
        'Date To',
        default=lambda self: date.today().replace(day=1) - relativedelta(days=1),
    )
    state = fields.Selection(
        [('choose', 'choose'), ('get', 'get')],
        default='choose',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    report = fields.Binary('Report', readonly=True)
    filename = fields.Char('File Name', size=128)
    line_ids = fields.One2many(
        'arclight_account_custom.report.hsn_summary.line',
        'report_id',
        string='HSN Summary Lines',
        readonly=True,
    )

    def _get_num(self, x):
        """Extract numeric value from string like '18%' or 'GST 18%'."""
        if not x:
            return 0
        s = ''.join(c for c in str(x) if c.isdigit() or c == '.')
        try:
            return float(s) if s else 0.0
        except ValueError:
            return 0.0

    def generate_hsn_summary(self):
        self.ensure_one()
        self.line_ids.unlink()
        from_date = self.date_from
        to_date = self.date_to

        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', from_date),
            ('invoice_date', '<=', to_date),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '!=', 'draft'),
            ('company_id', '=', self.company_id.id),
        ])

        hsn_data = {}

        for invoice in invoices:
            sign = -1 if invoice.move_type == 'out_refund' else 1
            foreign_curr = invoice.currency_id if invoice.currency_id != invoice.company_id.currency_id else None
            curr_rate_date = invoice.date or invoice.invoice_date
            company_curr = invoice.company_id.currency_id

            for line in invoice.invoice_line_ids.filtered(
                lambda l: l.product_id and l.product_id.default_code not in ('ADVANCE', 'CHARGES', 'DISCOUNT')
            ):
                prod = line.product_id
                hsn_code = prod.l10n_in_hsn_code or '999999'
                hsn_desc = getattr(prod, 'l10n_in_hsn_warning', None) or prod.name or 'Others'
                tax_rate = self._get_num(prod.taxes_id[0].name if prod.taxes_id else "0")
                uom = prod.uom_id
                line_uom = line.product_uom_id
                qty = line_uom._compute_quantity(line.quantity, uom) * sign

                amount = line.price_subtotal
                total_amount = line.price_total
                if foreign_curr:
                    amount = foreign_curr._convert(amount, company_curr, invoice.company_id, curr_rate_date) * sign
                    total_amount = foreign_curr._convert(total_amount, company_curr, invoice.company_id, curr_rate_date) * sign
                else:
                    amount *= sign
                    total_amount *= sign

                igst = cgst = sgst = cess = 0.0
                total_tax_line = total_amount - amount
                move = invoice
                if move.amount_untaxed and move.line_ids:
                    tax_lines = move.line_ids.filtered(lambda l: l.tax_line_id)
                    if tax_lines:
                        move_igst = move_cgst = move_sgst = move_cess = 0.0
                        for tl in tax_lines:
                            amt = abs(tl.balance) * sign
                            name = (tl.tax_line_id.name or '')
                            if 'IGST' in name.upper():
                                move_igst += amt
                            elif 'CGST' in name.upper() or 'CENTRAL' in name.upper():
                                move_cgst += amt
                            elif 'SGST' in name.upper() or 'UTGST' in name.upper() or 'STATE' in name.upper():
                                move_sgst += amt
                            elif 'cess' in name.lower():
                                move_cess += amt
                        line_share = (amount / move.amount_untaxed) if move.amount_untaxed else 0.0
                        igst = move_igst * line_share
                        cgst = move_cgst * line_share
                        sgst = move_sgst * line_share
                        cess = move_cess * line_share
                    else:
                        igst = total_tax_line
                else:
                    igst = total_tax_line

                type_supply = 'Services' if prod.type == 'service' else 'Goods'
                key = (hsn_code, uom, tax_rate, type_supply)
                if key in hsn_data:
                    v = hsn_data[key]
                    v['quantity'] += qty
                    v['total_value'] += total_amount
                    v['taxable_value'] += amount
                    v['igst'] += igst
                    v['cgst'] += cgst
                    v['sgst'] += sgst
                    v['cess'] += cess
                else:
                    uom_code = getattr(uom, 'l10n_in_code', None) or uom.name or ''
                    hsn_data[key] = {
                        'description': hsn_desc,
                        'uom_code': uom_code,
                        'quantity': qty,
                        'total_value': total_amount,
                        'taxable_value': amount,
                        'rate': tax_rate,
                        'igst': igst,
                        'cgst': cgst,
                        'sgst': sgst,
                        'cess': cess,
                        'uom_id': uom.id,
                    }

        rows = []

        def _row_sort_key(item):
            (hsn_code, uom, tax_rate, type_supply), vals = item
            supply_order = 1 if type_supply == 'Services' else 0
            return (supply_order, hsn_code, tax_rate)

        for (hsn_code, uom, tax_rate, type_supply), vals in sorted(hsn_data.items(), key=_row_sort_key):
            total_tax = vals['igst'] + vals['cgst'] + vals['sgst'] + vals['cess']
            rows.append({
                'hsn_code': hsn_code,
                'description': vals['description'],
                'type_supply': type_supply,
                'uom_code': vals['uom_code'],
                'quantity': vals['quantity'],
                'total_value': vals['total_value'],
                'rate': vals['rate'],
                'taxable_value': vals['taxable_value'],
                'igst': vals['igst'],
                'cgst': vals['cgst'],
                'sgst': vals['sgst'],
                'cess': vals['cess'],
                'total_tax': total_tax,
            })

        total_vouchers = len(invoices)
        invoices_with_hsn = set()
        for inv in invoices:
            for line in inv.invoice_line_ids.filtered(
                lambda l: l.product_id and l.product_id.default_code not in ('ADVANCE', 'CHARGES', 'DISCOUNT')
            ):
                if line.product_id and (line.product_id.l10n_in_hsn_code or line.product_id.type == 'service'):
                    invoices_with_hsn.add(inv.id)
                    break
        included_vouchers = len(invoices_with_hsn)
        incomplete_vouchers = max(0, total_vouchers - included_vouchers)

        fp = BytesIO()
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('HSN Summary')

        header_style = xlwt.easyxf("font: bold 1, height 220;")
        sub_header_style = xlwt.easyxf("font: bold 1; align: horiz center")
        sub_header_underline = xlwt.easyxf("font: bold 1; align: horiz center; borders: bottom thin")
        sub_header_left = xlwt.easyxf("font: bold 1; align: horiz left")
        sub_header_center = xlwt.easyxf("font: bold 1; align: horiz center")
        line_style = xlwt.easyxf("font: height 200;")
        total_style = xlwt.easyxf("font: bold 1; align: horiz right")
        num_style = xlwt.easyxf("font: height 200; align: horiz right", num_format_str='0')
        num_format_2dec = xlwt.easyxf("font: height 200; align: horiz right", num_format_str='0.00')
        num_format_qty = xlwt.easyxf("font: height 200; align: horiz right", num_format_str='0.00')
        rate_style = xlwt.easyxf("font: height 200; align: horiz center")

        col_widths = [3200, 3600, 7000, 2600, 2200, 3200, 3600, 2200, 3600, 3600, 3600, 3600, 2600]
        for col_idx in range(0, 13):
            if col_idx < len(col_widths):
                sheet.col(col_idx).width = min(col_widths[col_idx], 256 * 50)

        company = self.company_id
        col_start = 0
        row = 0
        sheet.write(row, col_start, company.name or '', header_style)
        row += 1
        line1 = ', '.join(p for p in [company.street, company.street2] if p)
        sheet.write(row, col_start, line1 or '', line_style)
        row += 1
        line2 = ', '.join(p for p in [
            company.city,
            company.state_id.name if company.state_id else '',
            company.zip,
        ] if p)
        if line2 or company.country_id:
            line2 = line2 + (', %s' % company.country_id.name if company.country_id else '')
        sheet.write(row, col_start, line2 or '', line_style)
        row += 1
        if getattr(company, 'cin', False):
            sheet.write(row, col_start, 'CIN No. %s' % company.cin, line_style)
            row += 1
        row += 1
        sheet.write(row, col_start, 'GSTR-1 - HSN/SAC Summary', header_style)
        row += 1
        period_str = '%s to %s' % (
            '%d-%s-%s' % (from_date.day, from_date.strftime('%b'), from_date.strftime('%y')) if from_date else '',
            '%d-%s-%s' % (to_date.day, to_date.strftime('%b'), to_date.strftime('%y')) if to_date else '',
        )
        sheet.write(row, col_start, period_str, line_style)
        row += 1
        sheet.write(row, col_start, 'HSN/SAC View', header_style)
        line_style_right = xlwt.easyxf("font: height 200; align: horiz right")
        sheet.write(row, 11, period_str, line_style_right)
        row += 1
        sheet.write(row, col_start, 'Particulars', sub_header_underline)
        sheet.write(row, 1, 'Voucher Count', sub_header_underline)
        row += 1
        sheet.write(row, col_start, 'Total Vouchers', total_style)
        sheet.write(row, 12, total_vouchers, num_style)
        row += 1
        sheet.write(row, col_start, 'Included in HSN/SAC Summary', line_style)
        sheet.write(row, 12, included_vouchers, num_style)
        row += 1
        sheet.write(row, col_start, 'Incomplete Information in HSN/SAC Summary (Corrections needed)', line_style)
        sheet.write(row, 12, incomplete_vouchers, num_style)
        row += 2

        sub_header_wrap = xlwt.easyxf(
            "font: bold 1; align: horiz center, wrap on; borders: bottom thin"
        )
        col_headers = [
            'HSN/SAC', 'Description', 'Type of Supply', 'UQC', 'Total Quantity',
            'Total Value', 'Tax Rate', 'Taxable Amount', 'Integrated Tax Amount',
            'Central Tax Amount', 'State Tax Amount', 'Cess Amount', 'Total Tax Amount',
        ]
        for col, label in enumerate(col_headers):
            sheet.write(row, col_start + col, label, sub_header_wrap)
        row += 1

        grand_total_value = grand_taxable = grand_igst = grand_cgst = grand_sgst = grand_cess = grand_tax = 0.0
        rate_num_style = xlwt.easyxf("font: height 200; align: horiz center", num_format_str='0.00')
        for r in rows:
            sheet.write(row, col_start + 0, r['hsn_code'] or '', line_style)
            sheet.write(row, col_start + 1, (r['description'] or '')[:50], line_style)
            sheet.write(row, col_start + 2, r['type_supply'] or 'Goods', line_style)
            uqc = r['uom_code'] or 'NA'
            if r['type_supply'] == 'Services' and not r['uom_code']:
                uqc = 'NA'
            sheet.write(row, col_start + 3, uqc, line_style)
            sheet.write(row, col_start + 4, r['quantity'], num_format_qty)
            sheet.write(row, col_start + 5, round(r['total_value'], 2), num_format_2dec)
            rate_val = r['rate']
            rate_num = round(float(rate_val), 2) if isinstance(rate_val, (int, float)) else 0.0
            sheet.write(row, col_start + 6, rate_num, rate_num_style)
            sheet.write(row, col_start + 7, round(r['taxable_value'], 2), num_format_2dec)
            if r['igst']:
                sheet.write(row, col_start + 8, round(r['igst'], 2), num_format_2dec)
            else:
                sheet.write(row, col_start + 8, 0.00, num_format_2dec)
            if r['cgst']:
                sheet.write(row, col_start + 9, round(r['cgst'], 2), num_format_2dec)
            else:
                sheet.write(row, col_start + 9, '', line_style)
            if r['sgst']:
                sheet.write(row, col_start + 10, round(r['sgst'], 2), num_format_2dec)
            else:
                sheet.write(row, col_start + 10, '', line_style)
            if r['cess']:
                sheet.write(row, col_start + 11, round(r['cess'], 2), num_format_2dec)
            else:
                sheet.write(row, col_start + 11, '', line_style)
            sheet.write(row, col_start + 12, round(r['total_tax'], 2), num_format_2dec)
            grand_total_value += r['total_value']
            grand_taxable += r['taxable_value']
            grand_igst += r['igst']
            grand_cgst += r['cgst']
            grand_sgst += r['sgst']
            grand_cess += r['cess']
            grand_tax += r['total_tax']
            row += 1

        total_num_style = xlwt.easyxf("font: bold 1; align: horiz right", num_format_str='0.00')
        sheet.write(row, col_start + 0, 'Grand Total', total_style)
        sheet.write(row, col_start + 5, round(grand_total_value, 2), total_num_style)
        sheet.write(row, col_start + 7, round(grand_taxable, 2), total_num_style)
        sheet.write(row, col_start + 8, round(grand_igst, 2), total_num_style)
        sheet.write(row, col_start + 9, round(grand_cgst, 2), total_num_style)
        sheet.write(row, col_start + 10, round(grand_sgst, 2), total_num_style)
        sheet.write(row, col_start + 11, round(grand_cess, 2), total_num_style)
        sheet.write(row, col_start + 12, round(grand_tax, 2), total_num_style)

        workbook.save(fp)
        out = base64.encodebytes(fp.getvalue())
        fname = 'HSN_Wise_Summary_%s_to_%s.xls' % (
            from_date.strftime('%Y%m%d') if from_date else '',
            to_date.strftime('%Y%m%d') if to_date else '',
        )
        self.write({
            'state': 'choose',
            'report': out,
            'filename': fname,
        })
        return {
            'name': 'HSN Wise Summary',
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=arclight_account_custom.report.hsn_summary&id=%s&filename_field=filename&field=report&download=true&filename=%s' % (
                self.id, fname
            ),
            'target': 'current',
        }


class HsnSummaryReportLine(models.TransientModel):
    _name = 'arclight_account_custom.report.hsn_summary.line'
    _description = 'HSN Wise Summary Line'

    report_id = fields.Many2one(
        'arclight_account_custom.report.hsn_summary',
        required=True,
        ondelete='cascade',
    )
    hsn_code = fields.Char('HSN Code')
    description = fields.Char('Description')
    uom_id = fields.Many2one('uom.uom', 'UoM')
    uom_code = fields.Char('UQC')
    quantity = fields.Float('Quantity', digits=(16, 4))
    total_value = fields.Monetary('Total Value', currency_field='currency_id')
    taxable_value = fields.Monetary('Taxable Value', currency_field='currency_id')
    rate = fields.Float('Rate %', digits=(5, 2))
    igst_amount = fields.Monetary('IGST', currency_field='currency_id')
    cgst_amount = fields.Monetary('CGST', currency_field='currency_id')
    sgst_amount = fields.Monetary('SGST', currency_field='currency_id')
    cess_amount = fields.Monetary('CESS', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        related='report_id.company_id.currency_id',
        readonly=True,
    )

