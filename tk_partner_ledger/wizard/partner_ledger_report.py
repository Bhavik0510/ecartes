# -*- coding: utf-8 -*-
from io import BytesIO
import base64
import xlwt
from odoo import fields, models, api
from odoo.exceptions import UserError


class PartnerLedgerGenerateReport(models.TransientModel):
    """
    Wizard for viewing the partner's ledger within a specified date range.
    Allows the user to generate the partner ledger report in PDF or Excel.
    """
    _name = 'partner.ledger.report'
    _description = "Partner Ledger Report"

    start_date = fields.Date(string="From Date", required=True)
    end_date = fields.Date(string="To Date", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    report_html = fields.Html(string="Preview", readonly=True, sanitize=False)

    @api.model
    def default_get(self, fields_list):
        result = super(PartnerLedgerGenerateReport, self).default_get(fields_list)
        result['partner_id'] = self._context.get('active_id')
        return result

    def btn_preview_action(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise UserError(self.env._("The start date must be earlier than the end date."))
        data = {
            'model': 'partner.ledger.report',
            'partner_id': self.partner_id.id,
            'form_data': {
                'start_date': fields.Date.to_string(self.start_date),
                'end_date': fields.Date.to_string(self.end_date),
            }
        }
        report_model = self.env['report.tk_partner_ledger.report_partner_ledger_pdf']
        vals = report_model._get_report_values([self.id], data=data)
        rendered_content = self.env['ir.qweb']._render('tk_partner_ledger.report_partner_ledger_main', vals)
        if isinstance(rendered_content, bytes):
            rendered_content = rendered_content.decode('utf-8')
        self.report_html = rendered_content

        return {
            'name': 'Partner Ledger',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.ledger.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'dialog_size': 'extra-large',
                'active_id': self.partner_id.id,
            },
        }

    def btn_pdf_action(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise UserError(self.env._("The start date must be earlier than the end date."))
        data = {
            'model': 'partner.ledger.report',
            'partner_id': self.partner_id.id,
            'form_data': {
                'start_date': fields.Date.to_string(self.start_date),
                'end_date': fields.Date.to_string(self.end_date),
            }
        }
        return self.env.ref('tk_partner_ledger.action_report_partner_ledger').report_action(self, data=data)

    def btn_excel_action(self):
        self.ensure_one()
        if self.start_date > self.end_date:
            raise UserError(self.env._("The start date must be earlier than the end date."))

        data = {
            'model': 'partner.ledger.report',
            'partner_id': self.partner_id.id,
            'form_data': {
                'start_date': self.start_date,
                'end_date': self.end_date,
            }
        }
        report_model = self.env['report.tk_partner_ledger.report_partner_ledger_pdf']
        vals = report_model._get_report_values(self.ids, data=data)

        workbook = xlwt.Workbook(encoding="UTF-8")
        sheet1 = workbook.add_sheet('Partner Ledger', cell_overwrite_ok=True)

        # Styles
        title_font = xlwt.Font()
        title_font.bold = True
        title_font.height = 280

        header_font = xlwt.Font()
        header_font.bold = True

        title_style = xlwt.easyxf('align: horiz center;')
        title_style.font = title_font

        center_style = xlwt.easyxf('align: horiz center;')
        bold_center_style = xlwt.easyxf('font: bold True; align: horiz center;')

        th_style = xlwt.easyxf('font: bold True; align: horiz left; borders: top thin, bottom thin;')
        th_right = xlwt.easyxf('font: bold True; align: horiz right; borders: top thin, bottom thin;')

        td_style = xlwt.easyxf('align: horiz left;')
        td_right = xlwt.easyxf('align: horiz right;')

        td_bold = xlwt.easyxf('font: bold True; align: horiz left;')
        td_bold_right = xlwt.easyxf('font: bold True; align: horiz right;')

        subtotal_style = xlwt.easyxf('align: horiz right; borders: top thin;')
        grand_total_style = xlwt.easyxf('font: bold True; align: horiz right; borders: top thin, bottom double;')

        # Set column widths
        sheet1.col(0).width = 4000   # Date
        sheet1.col(1).width = 11000  # Particulars
        sheet1.col(2).width = 4500   # Vch Type
        sheet1.col(3).width = 4500   # Vch No.
        sheet1.col(4).width = 4500   # Debit
        sheet1.col(5).width = 4500   # Credit

        row = 0
        # Company
        sheet1.write_merge(row, row, 0, 5, vals['company'].name or '', title_style)
        row += 1
        for addr in vals.get('company_address_lines', []):
            sheet1.write_merge(row, row, 0, 5, addr, center_style)
            row += 1
        if vals.get('company_cin'):
            sheet1.write_merge(row, row, 0, 5, f"CIN No. {vals['company_cin']}", center_style)
            row += 1

        row += 1
        # Partner
        sheet1.write_merge(row, row, 0, 5, vals['partner'].name or '', bold_center_style)
        row += 1
        sheet1.write_merge(row, row, 0, 5, "Ledger Account", center_style)
        row += 1
        for p_addr in vals.get('partner_address_lines', []):
            sheet1.write_merge(row, row, 0, 5, p_addr, center_style)
            row += 1

        row += 1
        # Period
        sheet1.write_merge(row, row, 0, 5, vals.get('period_label', ''), center_style)
        row += 2

        # Table Header
        sheet1.write(row, 0, 'Date', th_style)
        sheet1.write(row, 1, 'Particulars', th_style)
        sheet1.write(row, 2, 'Vch Type', th_style)
        sheet1.write(row, 3, 'Vch No.', th_right)
        sheet1.write(row, 4, 'Debit', th_right)
        sheet1.write(row, 5, 'Credit', th_right)
        row += 1

        # Opening Balance
        sheet1.write(row, 0, vals.get('opening_date', ''), td_style)
        sheet1.write(row, 1, vals.get('opening_particulars', ''), td_bold)
        sheet1.write(row, 2, '', td_style)
        sheet1.write(row, 3, '', td_right)
        sheet1.write(row, 4, vals.get('opening_debit_formatted', ''), td_bold_right)
        sheet1.write(row, 5, vals.get('opening_credit_formatted', ''), td_bold_right)
        row += 1

        # Transaction Rows
        for l in vals.get('lines', []):
            sheet1.write(row, 0, l.get('display_date', ''), td_style)
            sheet1.write(row, 1, l.get('particulars', ''), td_style)
            sheet1.write(row, 2, l.get('vch_type', ''), td_style)
            sheet1.write(row, 3, l.get('vch_no', ''), td_right)
            sheet1.write(row, 4, l.get('debit_formatted', ''), td_right)
            sheet1.write(row, 5, l.get('credit_formatted', ''), td_right)
            row += 1

        # Subtotal Row
        sheet1.write(row, 0, '', td_style)
        sheet1.write(row, 1, '', td_style)
        sheet1.write(row, 2, '', td_style)
        sheet1.write(row, 3, '', td_right)
        sheet1.write(row, 4, vals.get('subtotal_debit_formatted', ''), subtotal_style)
        sheet1.write(row, 5, vals.get('subtotal_credit_formatted', ''), subtotal_style)
        row += 1

        # Closing Balance Row
        sheet1.write(row, 0, '', td_style)
        sheet1.write(row, 1, vals.get('closing_particulars', ''), td_bold)
        sheet1.write(row, 2, '', td_style)
        sheet1.write(row, 3, '', td_right)
        sheet1.write(row, 4, vals.get('closing_debit_formatted', ''), td_right)
        sheet1.write(row, 5, vals.get('closing_credit_formatted', ''), td_right)
        row += 1

        # Grand Total Row
        sheet1.write(row, 0, '', td_style)
        sheet1.write(row, 1, '', td_style)
        sheet1.write(row, 2, '', td_style)
        sheet1.write(row, 3, '', td_right)
        sheet1.write(row, 4, vals.get('grand_total_debit_formatted', ''), grand_total_style)
        sheet1.write(row, 5, vals.get('grand_total_credit_formatted', ''), grand_total_style)

        stream = BytesIO()
        workbook.save(stream)

        filename = f"Partner_Ledger_{self.partner_id.name}.xls"
        output = base64.encodebytes(stream.getvalue())
        attachment_id = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': "binary",
            'public': False,
            'datas': output,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment_id.id}?download=true',
            'target': 'self',
        }
