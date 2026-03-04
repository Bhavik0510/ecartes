# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io

import xlsxwriter

from odoo import fields, http
from odoo.http import request


class PendingDcReportController(http.Controller):

    @http.route(
        '/arclight_account_custom/pending_dc_report_xlsx',
        type='http',
        auth='user',
        methods=['GET'],
    )
    def pending_dc_report_xlsx(self, date_from=None, date_to=None, **kwargs):
        """Generate and download Sales Bills Pending report as Excel."""
        if not date_from or not date_to:
            return request.not_found()
        # Parse dates (URL sends string e.g. 2026-03-01)
        try:
            dt_from = fields.Date.from_string(date_from)
            dt_to = fields.Date.from_string(date_to)
        except (TypeError, ValueError):
            return request.not_found()
        Report = request.env['pending.dc.report'].with_user(request.uid)
        wizard = Report.create({
            'date_from': dt_from,
            'date_to': dt_to,
        })
        data = wizard.get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Sales Bills Pending')

        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14})
        sub_head = workbook.add_format({'bold': True, 'font_size': 11})
        header_cell = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#6c757d', 'font_color': 'white', 'align': 'center',
        })
        cell_wrap = workbook.add_format({'font_size': 10, 'border': 1, 'text_wrap': True})
        cell_num = workbook.add_format({'font_size': 10, 'border': 1, 'num_format': '#,##0.00'})
        cell_num_right = workbook.add_format({'font_size': 10, 'border': 1, 'num_format': '#,##0.00', 'align': 'right'})
        company_name_fmt = workbook.add_format({'bold': True, 'font_size': 11})

        row = 0
        last_col = 8
        # Company details - one line per row, merged across all columns (A to last)
        sheet.merge_range(row, 0, row, last_col, data.get('company_name') or '', company_name_fmt)
        row += 1
        addr_line1 = ', '.join(filter(None, [data.get('company_street'), data.get('company_street2')]))
        if addr_line1:
            sheet.merge_range(row, 0, row, last_col, addr_line1.rstrip(','), cell_wrap)
            row += 1
        addr_line2 = ', '.join(filter(None, [
            data.get('company_city'),
            (data.get('company_state') or '') + ('-' + data.get('company_zip') if data.get('company_zip') else ''),
            data.get('company_country'),
        ]))
        if addr_line2.strip(','):
            sheet.merge_range(row, 0, row, last_col, addr_line2.strip(' ,'), cell_wrap)
            row += 1
        if data.get('company_cin'):
            sheet.merge_range(row, 0, row, last_col, 'CIN No. %s' % data.get('company_cin'), cell_wrap)
            row += 1
        row += 1
        sheet.merge_range(row, 0, row, last_col, 'Sales Bills Pending', company_name_fmt)
        row += 1
        sheet.merge_range(row, 0, row, last_col, 'Report Period: %s to %s' % (
            data.get('date_from_str', ''), data.get('date_to_str', '')
        ), sub_head)
        row += 2

        # Section 1: Goods Delivered but Bills not Made
        sheet.write(row, 0, 'Goods Delivered but Bills not Made', sub_head)
        row += 1
        cols = ['Date', 'Tracking Number', "Party's Name", 'Name of Item', 'Initial Quantity', 'Pending Quantity', 'Rate', 'Discount', 'Value']
        for c, col_name in enumerate(cols):
            sheet.write(row, c, col_name, header_cell)
        row += 1
        for line in data.get('goods_delivered_not_billed', []):
            sheet.write(row, 0, line.get('date_str') or '', cell_wrap)
            sheet.write(row, 1, line.get('tracking_number') or '', cell_wrap)
            sheet.write(row, 2, line.get('party_name') or '', cell_wrap)
            sheet.write(row, 3, line.get('item_name') or '', cell_wrap)
            sheet.write(row, 4, line.get('initial_qty', 0), cell_num_right)
            sheet.write(row, 5, line.get('pending_qty', 0), cell_num_right)
            r = line.get('rate')
            sheet.write(row, 6, r if r is not None else '', cell_wrap)
            d = line.get('discount')
            sheet.write(row, 7, '%.2f' % d if d is not None else '', cell_wrap)
            v = line.get('value')
            sheet.write(row, 8, v if v is not None else '', cell_wrap)
            row += 1
        # Total Value as last row below Goods Delivered but Bills not Made table (value in last column only)
        total_val = data.get('total_bills_not_delivered_value', 0)
        sheet.write(row, 8, total_val, cell_num_right)
        row += 2

        # Section 2: Bills Made but Goods not Delivered
        sheet.write(row, 0, 'Bills Made but Goods not Delivered', sub_head)
        row += 1
        for c, col_name in enumerate(cols):
            sheet.write(row, c, col_name, header_cell)
        row += 1
        for line in data.get('bills_made_not_delivered', []):
            sheet.write(row, 0, line.get('date_str') or '', cell_wrap)
            sheet.write(row, 1, line.get('tracking_number') or '', cell_wrap)
            sheet.write(row, 2, line.get('party_name') or '', cell_wrap)
            sheet.write(row, 3, line.get('item_name') or '', cell_wrap)
            sheet.write(row, 4, line.get('initial_qty', 0), cell_num_right)
            sheet.write(row, 5, line.get('pending_qty', 0), cell_num_right)
            sheet.write(row, 6, line.get('rate', 0), cell_num_right)
            sheet.write(row, 7, line.get('discount', 0), cell_num_right)
            sheet.write(row, 8, line.get('value', 0), cell_num_right)
            row += 1

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 18)
        sheet.set_column(2, 2, 28)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 8, 14)

        workbook.close()
        output.seek(0)
        filename = 'Sales_Bills_Pending_%s_to_%s.xlsx' % (dt_from, dt_to)
        return request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ],
        )
