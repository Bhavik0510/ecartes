# -*- coding: utf-8 -*-
import xlwt
import io
from io import StringIO
import base64
import time
from datetime import datetime, date, timedelta 
from dateutil import relativedelta
from odoo import models , fields , api , _  , exceptions


class Gstr_Return(models.Model):
    _inherit = 'gstr.return'

    def get_data(self):

        if not self.company_id.vat:
            raise exceptions.ValidationError(_("""Please Fill '%s' GSTIN number""") % self.company_id.name)
        
        workbook = xlwt.Workbook()
        title_style_center = xlwt.easyxf('align: horiz center ;font: name Times New Roman,bold off, italic off')
        title_style_left = xlwt.easyxf('font: name Times New Roman, height 200;align: horiz left ')
        title_style_right = xlwt.easyxf('font: name Times New Roman, height 200;align: horiz right ')
        title_style1_table_head_right = xlwt.easyxf('font: name Times New Roman,bold on, italic off, height 200;align: horiz right ;')
        title_style1_table_head_center = xlwt.easyxf('align: horiz center ;font: name Times New Roman,bold on, italic off, height 200')
        title_style1_table_head_left = xlwt.easyxf('align: horiz left ;font: name Times New Roman,bold on, italic off, height 200')

        row_date_count = 0

#        B2B Invoice
        sheet = workbook.add_sheet('b2b')
        # header in the sheet
        sheet.write(row_date_count, 0, 'No. of Recipients', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'No. of Invoices', title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, 'Total Invoice Value', title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8,)
        sheet.write(row_date_count, 9, 'Total Taxable Value', title_style1_table_head_right)
        sheet.write(row_date_count, 10, 'Total Cess', title_style1_table_head_right)
     
        row_date_count += 1
        
        customers = []
        total_invoice_value = 0.0
        total_taxable_value = 0.0
        total_cess_value = 0.0
        number_of_invoice = 0
         
        for invoice in self.b2b_invoice_ids:
            total_cess_value = total_cess_value + invoice.cess_amount
            total_invoice_value = total_invoice_value + invoice.invoice_value
            total_taxable_value = total_taxable_value + invoice.taxable_value
            if invoice.gstin_number not in customers:
                customers.append(invoice.gstin_number)
            number_of_invoice += 1
        number_of_customer = len(customers)
         
        sheet.write(row_date_count, 0, number_of_customer, title_style1_table_head_center)
        sheet.write(row_date_count, 1, number_of_invoice, title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8,)
        sheet.write(row_date_count, 9, total_taxable_value, title_style1_table_head_right)
        sheet.write(row_date_count, 10, total_cess_value, title_style1_table_head_right)
         
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'GSTIN/UIN of Recipient', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Invoice Number', title_style1_table_head_center)
        sheet.write(row_date_count, 2, 'Invoice date', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Invoice Value', title_style1_table_head_center)
        sheet.write(row_date_count, 4, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 5, 'Reverse Charge', title_style1_table_head_center)
        sheet.write(row_date_count, 6, 'Invoice Type', title_style1_table_head_center)
        sheet.write(row_date_count, 7, 'E-Commerce GSTIN', title_style1_table_head_center)
        sheet.write(row_date_count, 8, 'Rate', title_style1_table_head_center)
        sheet.write(row_date_count, 9, 'Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 10, 'Cess Amount', title_style1_table_head_center)
 
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.b2b_invoice_ids:
            
            dates = invoice.invoice_date
            dated = dates.strftime('%d %b %Y')
            
            sheet.write(row_date_count, 0, invoice.gstin_number, title_style_left)
            sheet.write(row_date_count, 1, invoice.invoice_id.name, title_style_left)
            sheet.write(row_date_count, 2, dated, title_style_center)
            sheet.write(row_date_count, 3, invoice.invoice_value, title_style_right)
            sheet.write(row_date_count, 4, invoice.state_name, title_style_left)
            sheet.write(row_date_count, 5, invoice.reverse_charge, title_style_center)  # need_to_fill
            sheet.write(row_date_count, 6, invoice.invoice_type, title_style_left)  # need_to_fill
            sheet.write(row_date_count, 7, invoice.e_commerce_gstin, title_style_left)  # need_to_fill
            sheet.write(row_date_count, 8, invoice.rate, title_style_right)
            sheet.write(row_date_count, 9, invoice.taxable_value, title_style_right)
            sheet.write(row_date_count, 10, invoice.cess_amount, title_style_right)
            row_date_count += 1  # increment row number
 
#         B2CS Invoice
        sheet = workbook.add_sheet('b2cs')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, 'Total Taxable Value', title_style1_table_head_right)
        sheet.write(row_date_count, 4, 'Total Cess' , title_style1_table_head_right)
        sheet.write(row_date_count, 5,)
         
        row_date_count += 1
         
        total_invoice_value = 0.0
        total_cess_value = 0.0
        number_of_invoice = 0
         
        for invoice in self.b2cs_invoice_ids:
            total_invoice_value = total_invoice_value + invoice.taxable_value
            total_cess_value = total_cess_value + invoice.cess_amount
            number_of_invoice += 1
         
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 4, total_cess_value, title_style1_table_head_right)
        sheet.write(row_date_count, 5,)
         
        row_date_count += 1
#        header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Type', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 2, 'Rate', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 4, 'Cess Amount', title_style1_table_head_center)
        sheet.write(row_date_count, 5, 'E-Commerce GSTIN', title_style1_table_head_center)
         
        row_date_count += 1
#        write multiple invoices to sheet
        for invoice in self.b2cs_invoice_ids:
            sheet.write(row_date_count, 0, invoice.type, title_style_left)
            sheet.write(row_date_count, 1, invoice.state_name, title_style_left)
            sheet.write(row_date_count, 2, invoice.rate, title_style_right)
            sheet.write(row_date_count, 3, invoice.taxable_value, title_style_right)
            sheet.write(row_date_count, 4, invoice.cess_amount, title_style_right)
            sheet.write(row_date_count, 5, invoice.e_commerce_gstin, title_style_left)
            row_date_count += 1  # increment row number
 
#        B2CL Invoice
        sheet = workbook.add_sheet('b2cl')
        row_date_count = 1
        sheet.write(row_date_count, 0, 'No. of Invoices', title_style1_table_head_center)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2, 'Total Inv Value', title_style1_table_head_center)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5, 'Total Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 6, 'Total Cess', title_style1_table_head_right)
        sheet.write(row_date_count, 7,)
 
        row_date_count += 1
 
        total_invoice_value = 0.0
        total_taxable_value = 0.0
        total_cess_value = 0.0
        number_of_invoice = 0
 
        for invoice in self.b2cl_invoice_ids:
            total_invoice_value = total_invoice_value + invoice.invoice_value
            total_taxable_value = total_taxable_value + invoice.taxable_value
            total_cess_value = total_cess_value + invoice.cess_amount
            number_of_invoice += 1  
 
        sheet.write(row_date_count, 0, number_of_invoice, title_style1_table_head_center)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5, total_taxable_value, title_style1_table_head_right)
        sheet.write(row_date_count, 6, total_cess_value, title_style1_table_head_right)  # need_to_fill
        sheet.write(row_date_count, 7,)
 
        row_date_count += 1
#        header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Invoice Number', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Invoice date', title_style1_table_head_center)
        sheet.write(row_date_count, 2, 'Invoice Value', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 4, 'Rate', title_style1_table_head_center)
        sheet.write(row_date_count, 5, 'Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 6, 'Cess Amount', title_style1_table_head_center)
        sheet.write(row_date_count, 7, 'E-Commerce GSTIN', title_style1_table_head_center)
 
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.b2cl_invoice_ids:
            
            dates = invoice.invoice_date
            dated = dates.strftime('%d %b %Y')
            
            sheet.write(row_date_count, 0, invoice.invoice_id.name, title_style_left)
            sheet.write(row_date_count, 1, dated, title_style_left)
            sheet.write(row_date_count, 2, invoice.invoice_value, title_style_right)
            sheet.write(row_date_count, 3, invoice.state_name, title_style_left)
            sheet.write(row_date_count, 4, invoice.rate, title_style_right)
            sheet.write(row_date_count, 5, invoice.taxable_value, title_style_right)
            sheet.write(row_date_count, 6, invoice.cess_amount, title_style_right)
            sheet.write(row_date_count, 7, invoice.e_commerce_gstin, title_style_left)
            row_date_count += 1  # increment row number
 
#        EXP Invoice
        sheet = workbook.add_sheet('exp')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, 'No. of Invoices', title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, 'Total Invoice Value', title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5, 'No. of Shipping Bill' , title_style1_table_head_center)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, 'Total Taxable Value', title_style1_table_head_right)
         
        row_date_count += 1
         
        total_invoice_value = 0.0
        total_taxable_value = 0.0
        number_of_invoice = 0
         
        for invoice in self.export_invoice_ids:
            total_invoice_value = total_invoice_value + invoice.invoice_value
            total_taxable_value = total_taxable_value + invoice.taxable_value
            number_of_invoice += 1
         
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, number_of_invoice, title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5, '', title_style1_table_head_center)  # need_to_fill
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, total_invoice_value, title_style1_table_head_right)
         
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Export Type', title_style1_table_head_left)
        sheet.write(row_date_count, 1, 'Invoice Number', title_style1_table_head_left)
        sheet.write(row_date_count, 2, 'Invoice date', title_style1_table_head_left)
        sheet.write(row_date_count, 3, 'Invoice Value', title_style1_table_head_right)
        sheet.write(row_date_count, 4, 'Port Code', title_style1_table_head_left)
        sheet.write(row_date_count, 5, 'Shipping Bill Number' , title_style1_table_head_left)
        sheet.write(row_date_count, 6, 'Shipping Bill Date', title_style1_table_head_left)
        sheet.write(row_date_count, 7, 'Rate', title_style1_table_head_right)
        sheet.write(row_date_count, 8, 'Total Taxable Value', title_style1_table_head_right)
         
        row_date_count += 1

        for invoice in self.export_invoice_ids:
            
            dated = invoice.invoice_date
            sheet.write(row_date_count, 0, invoice.export_type, title_style1_table_head_left)  # need_to_fill
            sheet.write(row_date_count, 1, invoice.invoice_id.name, title_style1_table_head_left)
            sheet.write(row_date_count, 2, dated, title_style1_table_head_left)
            sheet.write(row_date_count, 3, invoice.invoice_value, title_style1_table_head_right)
            sheet.write(row_date_count, 4, invoice.port_code, title_style1_table_head_center)  # need_to_fill
            sheet.write(row_date_count, 5, invoice.shipping_bill_number , title_style1_table_head_center)  # need_to_fill
            sheet.write(row_date_count, 6, invoice.shipping_bill_date, title_style1_table_head_left)  # need_to_fill
            sheet.write(row_date_count, 7, invoice.rate, title_style1_table_head_right)
            sheet.write(row_date_count, 8, invoice.taxable_value, title_style1_table_head_right)
            row_date_count += 1
 
#       EXEMP Invoice
        sheet = workbook.add_sheet('exemp')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, 'Total Nil Rated Supplies', title_style1_table_head_right)
        sheet.write(row_date_count, 2, 'Total Exempted Supplies', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Total Non-GST Supplies', title_style1_table_head_right)
         
        row_date_count += 1
         
        total_nil_rated_supplies = 0.0
        total_exempt_supplies = 0.0
        total_non_gst_supplies = 0.0
         
        for invoice in self.exempt_data_ids:
            total_nil_rated_supplies = total_nil_rated_supplies + invoice.nil_rated_supplies
            total_exempt_supplies = total_exempt_supplies + invoice.exempt_supplies
            total_non_gst_supplies = total_non_gst_supplies + invoice.non_gst_supplies
         
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, total_nil_rated_supplies, title_style1_table_head_right)
        sheet.write(row_date_count, 2, total_exempt_supplies, title_style1_table_head_right)
        sheet.write(row_date_count, 3, total_non_gst_supplies, title_style1_table_head_right)
         
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, 'Nil Rated Supplies', title_style1_table_head_right)
        sheet.write(row_date_count, 2, 'Exempted (other than nil rated/non GST supply )', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Non-GST supplies', title_style1_table_head_right)
         
        row_date_count += 1

        for invoice in self.exempt_data_ids:
            sheet.write(row_date_count, 0, invoice.description, title_style1_table_head_left)
            sheet.write(row_date_count, 1, invoice.nil_rated_supplies, title_style1_table_head_right)
            sheet.write(row_date_count, 2, invoice.exempt_supplies, title_style1_table_head_right)
            sheet.write(row_date_count, 3, invoice.non_gst_supplies, title_style1_table_head_right)
            row_date_count += 1  # increment row number
 
 
#       AT INVOICE
        sheet = workbook.add_sheet('at')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2, 'Total Advance Received', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Total Cess', title_style1_table_head_right)
 
        row_date_count += 1
 
        total_cess_amount = 0.0
        total_gross_advance_receipt = 0.0
 
        for invoice in self.advance_tax_ids:
            total_cess_amount = total_cess_amount + invoice.cess_amount
            total_gross_advance_receipt = total_gross_advance_receipt + invoice.gross_advance_receipt
 
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, total_cess_amount, title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, total_gross_advance_receipt, title_style1_table_head_right)
 
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Rate', title_style1_table_head_right)
        sheet.write(row_date_count, 2, 'Gross Advance Received', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Cess Amount', title_style1_table_head_right)
 
        row_date_count += 1
        
        for invoice in self.advance_tax_ids:
            sheet.write(row_date_count, 0, invoice.state_name, title_style1_table_head_center)
            sheet.write(row_date_count, 1, invoice.rate, title_style1_table_head_right)
            sheet.write(row_date_count, 2, invoice.gross_advance_receipt, title_style1_table_head_right)
            sheet.write(row_date_count, 3, invoice.cess_amount, title_style1_table_head_right)
            row_date_count += 1
            
#        ATADJ Invoice
        sheet = workbook.add_sheet('atadj')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2, 'Total Advance Adjusted', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Total Cess', title_style1_table_head_right)
         
        row_date_count += 1
 
        total_cess_amount = 0.0
        total_gross_advance_receipt = 0.0
 
        for invoice in self.advance_tax_ids:
            total_cess_amount = total_cess_amount + invoice.cess_amount
            total_gross_advance_receipt = total_gross_advance_receipt + invoice.gross_advance_receipt
 
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2, total_gross_advance_receipt, title_style1_table_head_right)
        sheet.write(row_date_count, 3, total_cess_amount, title_style1_table_head_right)
 
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Rate', title_style1_table_head_right)
        sheet.write(row_date_count, 2, 'Gross Advance Adjusted', title_style1_table_head_right)
        sheet.write(row_date_count, 3, 'Cess Amount', title_style1_table_head_right)
 
        row_date_count += 1
 
        for invoice in self.tax_adjust_ids:
            sheet.write(row_date_count, 0, invoice.state_name, title_style1_table_head_left)
            sheet.write(row_date_count, 1, invoice.rate, title_style1_table_head_right)
            sheet.write(row_date_count, 2, invoice.gross_advance_receipt, title_style1_table_head_right)
            sheet.write(row_date_count, 3, invoice.cess_amount, title_style1_table_head_right)
            row_date_count += 1

 
#       CDNR Invoice
        sheet = workbook.add_sheet('cdnr')
        row_date_count = 1
        sheet.write(row_date_count, 0, 'No. of Recipients', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'No. of Invoices', title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, 'No. of Notes/Vouchers', title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, 'Total Note/Refund Voucher Value', title_style1_table_head_right)
        sheet.write(row_date_count, 9,)
        sheet.write(row_date_count, 10, 'Total Taxable Value', title_style1_table_head_right)
        sheet.write(row_date_count, 11, 'Total Cess', title_style1_table_head_right)
        sheet.write(row_date_count, 12,)
 
        row_date_count += 1
 
        customers = []
        total_invoice_value = 0.0
        total_taxable_value = 0.0
        total_cess_amount = 0.0
        number_of_invoice = 0
 
        for invoice in self.cdnr_invoice_ids:
            total_invoice_value = total_invoice_value + invoice.voucher_value
            total_taxable_value = total_taxable_value + invoice.taxable_value
            total_cess_amount = total_cess_amount + invoice.cess_amount
            if invoice.gstin_number not in customers:
                customers.append(invoice.gstin_number)
            number_of_invoice += 1
        number_of_customer = len(customers)
 
        sheet.write(row_date_count, 0, number_of_customer, title_style1_table_head_center)
        sheet.write(row_date_count, 1, number_of_invoice, title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, number_of_invoice, title_style1_table_head_right)
        sheet.write(row_date_count, 4,)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, total_taxable_value, title_style1_table_head_right)
        sheet.write(row_date_count, 9,)
        sheet.write(row_date_count, 10, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 11, total_cess_amount, title_style1_table_head_right)
        sheet.write(row_date_count, 12,)
 
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'GSTIN/UIN of Recipient', title_style1_table_head_left)
        sheet.write(row_date_count, 1, 'Invoice/Advance Receipt Number', title_style1_table_head_left)
        sheet.write(row_date_count, 2, 'Invoice/Advance Receipt date', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Note/Refund Voucher Number', title_style1_table_head_left)
        sheet.write(row_date_count, 4, 'Note/Refund Voucher date', title_style1_table_head_center)
        sheet.write(row_date_count, 5, 'Document Type', title_style1_table_head_left)
        sheet.write(row_date_count, 6, 'Reason For Issuing document', title_style1_table_head_left)
        sheet.write(row_date_count, 7, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 8, 'Note/Refund Voucher Value', title_style1_table_head_right)
        sheet.write(row_date_count, 9, 'Rate', title_style1_table_head_center)
        sheet.write(row_date_count, 10, 'Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 11, 'Cess Amount', title_style1_table_head_right)
        sheet.write(row_date_count, 12, 'Pre GST', title_style1_table_head_right)
 
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.cdnr_invoice_ids:
            
            dates = invoice.invoice_date

            dated = dates
            
            voucher_dates = invoice.voucher_date
            voucher_dated = voucher_dates
            
            sheet.write(row_date_count, 0, invoice.gstin_number, title_style_left)
            sheet.write(row_date_count, 1, invoice.invoice_number, title_style_left)
            sheet.write(row_date_count, 2, dated, title_style_center)
            sheet.write(row_date_count, 3, invoice.voucher_id.name, title_style_right)
            sheet.write(row_date_count, 4, voucher_dated, title_style_left)
            sheet.write(row_date_count, 5, invoice.document_type, title_style_center)
            sheet.write(row_date_count, 6, invoice.reason, title_style_left)
            sheet.write(row_date_count, 7, invoice.state_name, title_style_left)  # add gst number from partner
            sheet.write(row_date_count, 8, invoice.voucher_value, title_style_right)
            sheet.write(row_date_count, 9, invoice.rate, title_style_right)
            sheet.write(row_date_count, 10, invoice.taxable_value, title_style_right)
            sheet.write(row_date_count, 11, invoice.cess_amount, title_style_right)
            sheet.write(row_date_count, 12, invoice.pre_gst, title_style_right)
            row_date_count += 1  # increment row number
 
 
#       CDNUR Invoice
        sheet = workbook.add_sheet('cdnur')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, 'No. of Notes/Vouchers', title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4, 'No. of Invoices', title_style1_table_head_right)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, 'Total Note Value', title_style1_table_head_right)
        sheet.write(row_date_count, 9,)
        sheet.write(row_date_count, 10, 'Total Taxable Value', title_style1_table_head_right)
        sheet.write(row_date_count, 11, 'Total Cess', title_style1_table_head_right)
        sheet.write(row_date_count, 12,)
     
        row_date_count += 1
              
        customers = []
        total_invoice_value = 0.0
        total_taxable_value = 0.0
        number_of_invoice = 0
 
        for invoice in self.cdnur_invoice_ids:
            total_invoice_value = total_invoice_value + invoice.voucher_value
            total_taxable_value = total_taxable_value + invoice.taxable_value
            total_cess_amount = total_cess_amount + invoice.cess_amount
            number_of_invoice += 1
         
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1, number_of_invoice, title_style1_table_head_center)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4, number_of_invoice, title_style1_table_head_right)
        sheet.write(row_date_count, 5,)
        sheet.write(row_date_count, 6,)
        sheet.write(row_date_count, 7,)
        sheet.write(row_date_count, 8, total_taxable_value, title_style1_table_head_right)
        sheet.write(row_date_count, 9,)
        sheet.write(row_date_count, 10, total_invoice_value, title_style1_table_head_right)
        sheet.write(row_date_count, 11, total_cess_amount, title_style1_table_head_right)
        sheet.write(row_date_count, 12,)
         
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'UR Type', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Note/Refund Voucher Number', title_style1_table_head_left)
        sheet.write(row_date_count, 2, 'Note/Refund Voucher date', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Document Type', title_style1_table_head_left)
        sheet.write(row_date_count, 4, 'Invoice/Advance Receipt Number', title_style1_table_head_left)
        sheet.write(row_date_count, 5, 'Invoice/Advance Receipt date', title_style1_table_head_center)
        sheet.write(row_date_count, 6, 'Reason For Issuing document', title_style1_table_head_left)
        sheet.write(row_date_count, 7, 'Place Of Supply', title_style1_table_head_center)
        sheet.write(row_date_count, 8, 'Note/Refund Voucher Value', title_style1_table_head_right)
        sheet.write(row_date_count, 9, 'Rate', title_style1_table_head_center)
        sheet.write(row_date_count, 10, 'Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 11, 'Cess Amount', title_style1_table_head_right)
        sheet.write(row_date_count, 12, 'Pre GST', title_style1_table_head_right)
         
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.cdnur_invoice_ids:
            
            dates = invoice.invoice_date
            dated = dates
            
            voucher_dates = invoice.voucher_date
            voucher_dated = voucher_dates
            
            sheet.write(row_date_count, 0, invoice.ur_type, title_style_left)
            sheet.write(row_date_count, 1, invoice.voucher_id.name, title_style_left)
            sheet.write(row_date_count, 2, voucher_dated, title_style_center)
            sheet.write(row_date_count, 3, invoice.document_type, title_style_center)
            sheet.write(row_date_count, 4, invoice.invoice_number, title_style_left)
            sheet.write(row_date_count, 5, dated, title_style_center)
            sheet.write(row_date_count, 6, invoice.reason, title_style_left)
            sheet.write(row_date_count, 7, invoice.state_name, title_style_left)
            sheet.write(row_date_count, 8, invoice.voucher_value, title_style_right)
            sheet.write(row_date_count, 9, invoice.rate, title_style_right)
            sheet.write(row_date_count, 10, invoice.taxable_value, title_style_right)
            sheet.write(row_date_count, 11, invoice.cess_amount, title_style_right)
            sheet.write(row_date_count, 12, invoice.pre_gst, title_style_right)
            row_date_count += 1
 
#        HSN Invoice
        sheet = workbook.add_sheet('hsn')
        row_date_count = 1
        sheet.write(row_date_count, 0, 'No. of HSN', title_style1_table_head_center)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4, 'Total Value', title_style1_table_head_center)
        sheet.write(row_date_count, 5, 'Total Taxable Value', title_style1_table_head_center)
        sheet.write(row_date_count, 6, 'Total Integrated Tax', title_style1_table_head_right)
        sheet.write(row_date_count, 7, 'Total Central Tax', title_style1_table_head_right)
        sheet.write(row_date_count, 8, 'Total State/UT Tax', title_style1_table_head_right)
        sheet.write(row_date_count, 9, 'Total Cess', title_style1_table_head_right)
        
        row_date_count += 1
        
        hsn = []
        total = 0.0
        total_taxable_value = 0.0
        total_igst = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        
        if self.hsn_data_ids:
            for data in self.hsn_data_ids:
                total = total + data.total_value
                total_taxable_value = total_taxable_value + data.taxable_value
                total_cgst = total_cgst + data.cgst
                total_sgst = total_sgst + data.sgst
                total_igst = total_igst + data.igst
                total_cess_amount = total_cess_amount + data.cess_amount
                if data.hsn_code not in hsn:
                    hsn.append(data.hsn_code)
        number_of_hsn = len(hsn)
                    
 
        sheet.write(row_date_count, 0, number_of_hsn, title_style1_table_head_center)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3,)
        sheet.write(row_date_count, 4, total, title_style1_table_head_center)
        sheet.write(row_date_count, 5, total_taxable_value, title_style1_table_head_center)
        sheet.write(row_date_count, 6, total_igst, title_style1_table_head_right)
        sheet.write(row_date_count, 7, total_cgst, title_style1_table_head_right)
        sheet.write(row_date_count, 8, total_sgst, title_style1_table_head_right)
        sheet.write(row_date_count, 9, total_cess_amount, title_style1_table_head_right)
 
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'HSN', title_style1_table_head_center)
        sheet.write(row_date_count, 1, 'Description', title_style1_table_head_center)
        sheet.write(row_date_count, 2, 'UQC', title_style1_table_head_center)
        sheet.write(row_date_count, 3, 'Total Quantity', title_style1_table_head_center)
        sheet.write(row_date_count, 4, 'Total Value', title_style1_table_head_right)
        sheet.write(row_date_count, 5, 'Taxable Value', title_style1_table_head_right)
        sheet.write(row_date_count, 6, 'Integrated Tax Amount', title_style1_table_head_right)
        sheet.write(row_date_count, 7, 'Central Tax Amount', title_style1_table_head_right)
        sheet.write(row_date_count, 8, 'State/UT Tax Amount', title_style1_table_head_right)
        sheet.write(row_date_count, 9, 'Cess Amount', title_style1_table_head_center)
 
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.hsn_data_ids:
            # for invoice in hsn:
            sheet.write(row_date_count, 0, invoice.hsn_code, title_style_left)
            sheet.write(row_date_count, 1, invoice.description, title_style_left)
            sheet.write(row_date_count, 2, 'dfdfdfdf', title_style_center)
            sheet.write(row_date_count, 3, invoice.total_quantity, title_style_right)
            sheet.write(row_date_count, 4, invoice.total_value, title_style_left)
            sheet.write(row_date_count, 5, invoice.taxable_value, title_style_center)
            sheet.write(row_date_count, 6, invoice.igst, title_style_left)
            sheet.write(row_date_count, 7, invoice.sgst, title_style_left)  # add gst number from partner
            sheet.write(row_date_count, 8, invoice.cgst, title_style_right)
            sheet.write(row_date_count, 9, invoice.cess_amount, title_style_right)
            row_date_count += 1  # increment row number
 
#        DOCS Sheet
        sheet = workbook.add_sheet('docs')
        row_date_count = 1
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, 'Total Number', title_style1_table_head_right)
        sheet.write(row_date_count, 4, 'Total Value', title_style1_table_head_right)
     
        row_date_count += 1
        
        total_invoice = total_cancel = 0.0
        
        for invoice in self.docs_data_ids:
            total_invoice =  total_invoice + invoice.total
            total_cancel =  total_cancel + invoice.cancelled
        
        sheet.write(row_date_count, 0,)
        sheet.write(row_date_count, 1,)
        sheet.write(row_date_count, 2,)
        sheet.write(row_date_count, 3, total_invoice, title_style1_table_head_right)
        sheet.write(row_date_count, 4, total_cancel, title_style1_table_head_right)
 
        row_date_count += 1
        # header of the Multiple invoice
        sheet.write(row_date_count, 0, 'Nature  of Document', title_style1_table_head_left)
        sheet.write(row_date_count, 1, 'Sr. No. From', title_style1_table_head_left)
        sheet.write(row_date_count, 2, 'Sr. No. To', title_style1_table_head_left)
        sheet.write(row_date_count, 3, 'Total Number', title_style1_table_head_right)
        sheet.write(row_date_count, 4, 'Cancelled', title_style1_table_head_right)
 
        row_date_count += 1
        # write multiple invoices to sheet
        for invoice in self.docs_data_ids:
            sheet.write(row_date_count, 0, invoice.nature_of_document, title_style_left)
            sheet.write(row_date_count, 1, invoice.no_from, title_style_left)
            sheet.write(row_date_count, 2, invoice.no_to, title_style_center)
            sheet.write(row_date_count, 3, invoice.total, title_style_right)
            sheet.write(row_date_count, 4, invoice.cancelled, title_style_left)
            row_date_count += 1  # increment row number

        stream = io.BytesIO()
        
        workbook.save(stream)
        attach_id = self.env['v.excel.output'].create({
            'name' : self.name,
            'filename': base64.encodestring(stream.getvalue())
        })
        return attach_id.download()
