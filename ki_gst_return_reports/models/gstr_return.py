# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, date, timedelta 
import time
from dateutil import relativedelta
from odoo.exceptions import UserError



class Gstr_Return(models.Model):
    _name = 'gstr.return'
    _description = "GSTR Return"

    name = fields.Char(
        string="Name",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        readonly=True,
    )
    gstin = fields.Char(
        string='GSTIN',
        readonly=True,
        compute='compute_gst_number',
        store=True,
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=str(datetime.now() + relativedelta.relativedelta(months=-1, day=1))[:10]
    )
    end_date = fields.Date(string='End Date',
        required=True,
        default=str(datetime.now() + relativedelta.relativedelta(day=1, days=-1))[:10]
    )

    state = fields.Selection([
            ('draft', 'Draft'),
            ('progress', 'Progress'),
            ('checking', 'Checking'),
            ('cancel', 'Cancel'),
            ('done', 'Done'),
        ],
        string='Status',
        readonly=True,
        default='draft',
        copy=False,
    )

    # One 2 Many fields.
    b2b_invoice_ids = fields.One2many('b2b.invoice', 'gst_return_id', string='B2B Invoice')
    b2cs_invoice_ids = fields.One2many('b2cs.invoice', 'gst_return_id', string='B2cs Invoice')
    b2cl_invoice_ids = fields.One2many('b2cl.invoice', 'gst_return_id', string='B2cl Invoice')
    cdnr_invoice_ids = fields.One2many('cdnr.invoice', 'gst_return_id', string='Cdnr Invoice')
    cdnur_invoice_ids = fields.One2many('cdnur.invoice', 'gst_return_id', string='Cnur Invoice')
    export_invoice_ids = fields.One2many('export.invoice', 'gst_return_id', string='Export Invoice')
    advance_tax_ids = fields.One2many('advance.tax', 'gst_return_id', string='Advance Tax Invoice')
    tax_adjust_ids = fields.One2many('tax.adjustment', 'gst_return_id', string='Tax Adjust Invoice')
    exempt_data_ids = fields.One2many('exempt.data', 'gst_return_id', string='Exempt Invoice')
    hsn_data_ids = fields.One2many('hsn.data', 'gst_return_id', string='HSN Data Invoice')
    docs_data_ids = fields.One2many('docs.data', 'gst_return_id', string='Docs Data Invoice')

    def action_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
        return True
    
    def action_submit(self):
        for rec in self:
            rec.write({'state': 'done'})
        return True

    @api.depends('company_id', 'company_id.vat')
    def compute_gst_number(self):
        for rec in self:
            rec.gstin = rec.company_id.vat

    @api.model
    def get_lines(self, invoice):
        result = {}
        for line in invoice.invoice_line_ids:
            if not line.product_id.name == 'Down payment':
                tax_rate = 0
                for tax in line.tax_ids:
                    tax_rate = tax_rate + tax.amount
                if tax_rate not in result:
                    result[tax_rate] = line.price_subtotal
                else:
                    total = result[tax_rate]
                    result[tax_rate] = total + line.price_subtotal
        return result

    def compute_gstr(self):
        today = date.today()
        tax = 0
        gst_start_date = date(2017, 7, 1)
        for rec in self:

            if not rec.gstin:
                raise UserError('Please Add the GST Number')

            start = rec.start_date
            datee = start
            name = str(datee.month) + '_' + str(datee.year)
            if datee.month < 10:
                name = '0' + name

            rec.name = name + '_' + str(rec.gstin)

            rec.write({'state': 'progress'})

    #        Remove old Data
            rec.b2b_invoice_ids.unlink()
            rec.b2cs_invoice_ids.unlink()
            rec.b2cl_invoice_ids.unlink()
            rec.cdnr_invoice_ids.unlink()
            rec.cdnur_invoice_ids.unlink()
            rec.export_invoice_ids.unlink()
            rec.advance_tax_ids.unlink()
            rec.tax_adjust_ids.unlink()
            rec.exempt_data_ids.unlink()
            rec.hsn_data_ids.unlink()
            rec.docs_data_ids.unlink()
            print("/c/c/c/c/c/c/c/")

#       B2B Invoice
            all_invoices = self.env['account.move'].search([('company_id', '=', rec.company_id.id),
                                                               ('state', 'not in', ('cancel', 'draft')),
                                                               ('move_type', '=', 'out_invoice'),
                                                               ('invoice_date', '>=', rec.start_date),
                                                               ('invoice_date', '<=', rec.end_date)])

            print("...c.c.c.....", all_invoices)
            b2b_invoices = all_invoices
            B2CS = {}
            hsn = {}
            for invoice in b2b_invoices:
                if invoice.partner_id.vat and invoice.partner_id.country_id == invoice.company_id.country_id:
                    amount_total = 0.0
                    price = 0.0
                    result = {}
                    for line in invoice.invoice_line_ids:
                        if not line.product_id.name == 'Down payment':
                            tax_rate = 0
                            for tax in line.tax_ids:
                                tax_rate = tax_rate + tax.amount
                                price = (line.price_subtotal) + ((line.price_subtotal * tax_rate) / 100)
                            if tax_rate not in result:
                                result[tax_rate] = line.price_subtotal
                            else:
                                total = result[tax_rate]
                                result[tax_rate] = total + line.price_subtotal
                            amount_total = amount_total + price

                    for res in result:
                        if invoice.partner_id.state_id.l10n_in_tin:
                            state_name = invoice.partner_id.state_id.l10n_in_tin
                        else:
                            state_name = '' + '-' + invoice.partner_id.state_id.name
                        vals = {
                            'gstin_number': invoice.partner_id.vat,
                            'invoice_id': invoice.id,
                            'invoice_date': invoice.invoice_date,
                            'invoice_value': amount_total,
                            'state_name': state_name,
                            'reverse_charge': '',
                            'invoice_type': 'Regular',
                            'e_commerce_gstin': '',
                            'rate': res,
                            'taxable_value': result[res],
                            'cess_amount': '',
                            'gst_return_id': rec.id,
                           }
                        self.env['b2b.invoice'].create(vals)

                # B2CS 
                if not invoice.partner_id.vat:
                    if invoice.partner_id.country_id == invoice.company_id.country_id:
                        if invoice.partner_id.state_id != invoice.company_id.state_id:

                            amount_untax = amount_total = 0.0
                            price = 0.0
                            result = {}
                            for line in invoice.invoice_line_ids:
                                if not line.product_id.name == 'Down payment':
                                    tax_rate = 0
                                    for tax in line.tax_ids:
                                        tax_rate = tax_rate + tax.amount
                                        price = (line.price_subtotal)
                                    amount_untax = amount_untax + price

                            if amount_untax <= 250000:
                                if invoice.partner_id.state_id.l10n_in_tin:

                                    if invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name not in B2CS:
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name] = {}
                                    if not invoice.e_commerce_gst:
                                        if 'OE' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE'] = {}
                                        if 'other' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'] = {}
                                        for line in invoice.invoice_line_ids:
                                            if not line.product_id.name == 'Down payment':
                                                result = {}
                                                tax_rate = 0
                                                for tax in line.tax_ids:
                                                    tax_rate = tax_rate + tax.amount
                                                if tax_rate not in result:
                                                    result[tax_rate] = line.price_subtotal
                                                else:
                                                    total = result[tax_rate]
                                                    result[tax_rate] = total + line.price_subtotal
                                        for rate in result:
                                            if rate not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other']:
                                                B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'][rate] = {'taxable_value': 0.0, 'cess_amount': 0.0, }
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'][rate]['taxable_value'] += result[rate]
                                    else:
                                        if 'E' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'] = {}
                                        if invoice.e_commerce_gst not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E']:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst] = {}
                                        for line in invoice.invoice_line_ids:
                                            if not line.product_id.name == 'Down payment':
                                                result = {}
                                                tax_rate = 0
                                                for tax in line.tax_ids:
                                                    tax_rate = tax_rate + tax.amount
                                                if tax_rate not in result:
                                                    result[tax_rate] = line.price_subtotal
                                                else:
                                                    total = result[tax_rate]
                                                    result[tax_rate] = total + line.price_subtotal
                                        for rate in result:
                                            if rate not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst]:
                                                B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst][rate] = {'taxable_value': 0.0, 'cess_amount': 0.0, }
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst][rate]['taxable_value'] += result[rate]
                        else:
                            if invoice.partner_id.state_id.l10n_in_tin:
                                if invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name not in B2CS:
                                    B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name] = {}
                                if not invoice.e_commerce_gst:
                                    if 'OE' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]:
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE'] = {}
                                    if 'other' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']:
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'] = {}
                                    result = {}
                                    for line in invoice.invoice_line_ids:
                                        if not line.product_id.name == 'Down payment':
                                            tax_rate = 0
                                            for tax in line.tax_ids:
                                                tax_rate = tax_rate + tax.amount
                                            if tax_rate not in result:
                                                result[tax_rate] = line.price_subtotal
                                            else:
                                                total = result[tax_rate]
                                                result[tax_rate] = total + line.price_subtotal
                                    for rate in result:
                                        if rate not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other']:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'][rate] = {'taxable_value': 0.0, 'cess_amount': 0.0, }
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['OE']['other'][rate]['taxable_value'] += result[rate]
                                else:
                                    if 'E' not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]:
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'] = {}
                                    if invoice.e_commerce_gst not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E']:
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst] = {}
                                    for line in invoice.invoice_line_ids:
                                        if not line.product_id.name == 'Down payment':
                                            result = {}
                                            tax_rate = 0
                                            for tax in line.tax_ids:
                                                tax_rate = tax_rate + tax.amount
                                            if tax_rate not in result:
                                                result[tax_rate] = line.price_subtotal
                                            else:
                                                total = result[tax_rate]
                                                result[tax_rate] = total + line.price_subtotal
                                    for rate in result:
                                        if rate not in B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst]:
                                            B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst][rate] = {'taxable_value': 0.0, 'cess_amount': 0.0, }
                                        B2CS[invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name]['E'][invoice.e_commerce_gst][rate]['taxable_value'] += result[rate]

                # b2cl 
                if invoice.partner_id.country_id == invoice.company_id.country_id:
                    if invoice.partner_id.state_id != invoice.company_id.state_id and not invoice.partner_id.vat:

                        amount_untax = amount_total = 0.0
                        price = 0.0
                        result = {}
                        for line in invoice.invoice_line_ids:
                            if not line.product_id.name == 'Down payment':
                                tax_rate = 0
                                tax_r = 0
                                for tax in line.tax_ids:
                                    tax_rate = tax_rate + tax.amount
                                    price = (line.price_subtotal)
                                    tax_r = ((line.price_subtotal * tax_rate) / 100)
                                amount_total = amount_total + price + tax_r
                                amount_untax = amount_untax + price

                        if amount_untax > 250000:
                            if invoice.e_commerce_gst:
                                e_commerce_gst = invoice.e_commerce_gst
                            else:
                                e_commerce_gst = ''
                            for line in invoice.invoice_line_ids:
                                if not line.product_id.name == 'Down payment':
                                    result = {}
                                    tax_rate = 0
                                    for tax in line.tax_ids:
                                        tax_rate = tax_rate + tax.amount
                                    if tax_rate not in result:
                                        result[tax_rate] = line.price_subtotal
                                    else:
                                        total = result[tax_rate]
                                        result[tax_rate] = total + line.price_subtotal
                            for res in result:
                                if invoice.partner_id.state_id.l10n_in_tin:
                                    state_name = invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name
                                else:
                                    state_name = invoice.partner_id.state_id.name

                                vals = {'invoice_id': invoice.id,
                                        'invoice_date': invoice.invoice_date,
                                        'invoice_value': amount_total,
                                        'state_name': state_name,
                                        'rate': res,
                                        'taxable_value': result[res],
                                        'cess_amount': '',
                                        'e_commerce_gstin': e_commerce_gst,
                                        'gst_return_id': rec.id,
                                        }
                                self.env['b2cl.invoice'].create(vals)
                #       Export Invoice
                if invoice.partner_id.country_id != invoice.company_id.country_id:
                    result = rec.get_lines(invoice)
                    for res in result:
                        if res == 0.0:
                            type = 'WOPAY'
                        else:
                            type = 'WPAY'
                        vals = {'export_type': type,
                                'invoice_id': invoice.id,
                                'invoice_date': invoice.invoice_date,
                                'invoice_value': invoice.amount_total,
                                'port_code': '',
                                'shipping_bill_number': '',
    #                             'shipping_bill_date': 'shipping_bill_date',
                                'rate': res,
                                'taxable_value': result[res],
                                'gst_return_id': rec.id,
                                }
                        self.env['export.invoice'].create(vals)
                #       Advance Tax  
                for line in invoice.invoice_line_ids:
                    if line.product_id.name == 'Down payment' and line.price_subtotal > 0.0:
                        origin = invoice.invoice_origin

                        inv = self.env['account.move'].search([('id', '!=', invoice.id),
                                                                  ('invoice_origin', '=', origin),
                                                                  ('state', 'not in', ('cancel', 'draft')),
                                                                  ('move_type', '=', 'out_invoice'),
                                                                  ('invoice_date', '>=', rec.start_date),
                                                                  ('invoice_date', '<=', rec.end_date)])

                        if inv:
                            flag = False
                            for line in inv.invoice_line_ids:
                                if line.product_id.name == 'Down payment' and line.price_subtotal < 0.0:
                                    flag = True
                                    break
                            if flag == True:
                                break
                        if line.price_subtotal > 0.0:
                            tax_rate = 0
                            for tax in line.tax_ids:
                                tax_rate = tax_rate + tax.amount
                            if invoice.partner_id.state_id.l10n_in_tin:
                                state_name = invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name
                            else:
                                state_name = invoice.partner_id.state_id.name
                            vals = {
                                'state_name': state_name,
                                'rate': tax_rate,
                                'gross_advance_receipt': line.price_subtotal,
                                'cess_amount': '',
                                'gst_return_id': rec.id,
                                }
                            self.env['advance.tax'].create(vals)
                    #     Advance Tax Adjustment
                    if line.product_id.name == 'Down payment' and line.price_subtotal < 0.0:
                        origin = invoice.invoice_origin

                        inv = self.env['account.move'].search([('id', '!=', invoice.id),
                                                                  ('invoice_origin', '=', origin),
                                                                  ('state', 'not in', ('cancel', 'draft')),
                                                                  ('move_type', '=', 'out_invoice'),
                                                                  ('invoice_date', '>=', rec.start_date),
                                                                  ('invoice_date', '<=', rec.end_date)])
                        if inv:
                            flag = False
                            for line in inv.invoice_line_ids:
                                if line.product_id.name == 'Down payment' and line.price_subtotal > 0.0:
                                    flag = True
                                    break
                            if flag == True:
                                break
                        elif line.price_subtotal < 0.0:
                            price = (line.price_subtotal * -1.0)
                            tax_rate = 0
                            for tax in line.tax_ids:
                                tax_rate = tax_rate + tax.amount
                            if invoice.partner_id.state_id:
                                if invoice.partner_id.state_id.l10n_in_tin:
                                    state_name = invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name
                                else:
                                    state_name = invoice.partner_id.state_id.name
                            vals = {
                                'state_name': state_name,
                                'rate': tax_rate,
                                'gross_advance_receipt': price,
                                'cess_amount': '',
                                'gst_return_id': rec.id,
                                }
                            self.env['tax.adjustment'].create(vals)
                    #       HSN Data
                    if not line.product_id.name == 'Down payment':
                            if line.product_id not in hsn:
                                hsn[line.product_id] = {}
                                hsn[line.product_id].update({
                                                            'hsn': line.product_id.l10n_in_hsn_code,
                                                            'name': line.product_id.name,
                                                            'quantity': line.quantity,
                                                            'total_value': line.price_subtotal,
                                                            'uqc': line.product_id.uom_id.id,
                                                            'taxable_value': 0.0,
                                                            'CGST': 0.0,
                                                            'SGST': 0.0,
                                                            'IGST': 0.0,
                                                            'cess': 0.0,
                                                            })
                                if line.tax_ids:
                                    hsn[line.product_id]['taxable_value'] += line.price_subtotal
                                for tax in line.tax_ids:
                                    if tax.tax_group_id.name == 'CGST':
                                        cgst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['CGST'] += cgst
                                    if tax.tax_group_id.name == 'SGST':
                                        sgst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['SGST'] += sgst
                                    if tax.tax_group_id.name == 'IGST':
                                        igst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['IGST'] += igst
                                    if not tax.tax_group_id.name:
                                        cess = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['cess'] += cess
                            else:
                                hsn[line.product_id]['quantity'] += line.quantity
                                hsn[line.product_id]['total_value'] += line.price_subtotal
                                if line.tax_ids:
                                    hsn[line.product_id]['taxable_value'] += line.price_subtotal
                                for tax in line.tax_ids:
                                    if tax.tax_group_id.name == 'CGST':
                                        cgst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['CGST'] += cgst
                                    if tax.tax_group_id.name == 'SGST':
                                        sgst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['SGST'] += sgst
                                    if tax.tax_group_id.name == 'IGST':
                                        igst = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['IGST'] += igst
                                    if not tax.tax_group_id.name:
                                        cess = (line.price_subtotal * tax.amount) / 100
                                        hsn[line.product_id]['cess'] += cess

            for state in B2CS:
                for type in B2CS[state]:
                    for gst in B2CS[state][type]:
                        for rate in B2CS[state][type][gst]:
                            if gst == 'other':
                                e_comm = ''
                            else:
                                e_comm = gst
                            vals = {
                                    'type': type,
                                    'state_name': state,
                                    'rate': rate,
                                    'taxable_value': B2CS[state][type][gst][rate].get('taxable_value'),
                                    'cess_amount': B2CS[state][type][gst][rate].get('cess_amount'),
                                    'e_commerce_gstin': e_comm,
                                    'gst_return_id': rec.id,
                                    }
                            self.env['b2cs.invoice'].create(vals)

            for product in hsn:
                vals = {'hsn_code': hsn[product].get('hsn'),
                        'description': hsn[product].get('name'),
                        'uom_id':hsn[product].get('uqc'),
                        'total_quantity':hsn[product].get('quantity'),
                        'total_value':hsn[product].get('total_value'),
                        'taxable_value': hsn[product].get('taxable_value'),
                        'igst': hsn[product].get('igst'),
                        'sgst':hsn[product].get('sgst'),
                        'cgst':hsn[product].get('cgst'),
                        'cess_amount': hsn[product].get('cess'),
                        'gst_return_id': rec.id,
                        }
                self.env['hsn.data'].create(vals)

          

#       CDNR Invoice
            cdnr_invoices = self.env['account.move'].search([('company_id', '=', rec.company_id.id),
                                                                ('state', 'not in', ('cancel', 'draft')),
                                                                ('invoice_date', '>=', rec.start_date),
                                                                ('invoice_date', '<=', rec.end_date),
                                                                ('move_type', 'in', ('in_refund', 'out_refund'))])

            for invoice in cdnr_invoices:
                if invoice.partner_id.vat:
                    inv = False
                    pre_gst = ''
                    if invoice.invoice_origin:
                        inv = invoice.reversed_entry_id

                        if inv.invoice_date:

                            if inv.invoice_date < gst_start_date:
                                pre_gst = 'Y'
                            else:
                                pre_gst = 'N'

                    if invoice.move_type == 'in_refund':
                        document_type = 'C'
                    else:
                        document_type = 'D'

                    result = rec.get_lines(invoice)

                    for res in result:
                        vals = {'gstin_number':invoice.partner_id.vat,
                                'invoice_number': invoice.invoice_origin,
                                'invoice_date': inv.invoice_date if inv else False,
                                'voucher_id':invoice.id,
                                'voucher_date':invoice.invoice_date,
                                'document_type':document_type,
                                'reason':invoice.name,
                                'state_name': invoice.partner_id.state_id.l10n_in_tin if invoice.partner_id.state_id.l10n_in_tin else '' + '-' + invoice.partner_id.state_id.name,
                                'voucher_value': invoice.amount_total,
                                'rate': res,
                                'taxable_value': result[res],
                                'cess_amount':'',
                                'pre_gst':pre_gst,
                                'gst_return_id': rec.id,
                                }
                        self.env['cdnr.invoice'].create(vals)

#       CDNUR Invoice
            cdnur_invoices = self.env['account.move'].search([('company_id', '=', rec.company_id.id),
                                                                 ('state', 'not in', ('cancel', 'draft')),
                                                                 ('invoice_date', '>=', rec.start_date),
                                                                 ('invoice_date', '<=', rec.end_date),
                                                                 ('move_type', 'in', ('in_refund', 'out_refund'))])
            for invoice in cdnur_invoices:
                if invoice.partner_id.country_id == invoice.company_id.country_id:
                    state_name = invoice.partner_id.state_id.l10n_in_tin + '-' + invoice.partner_id.state_id.name
                else:
                    state_name = invoice.partner_id.state_id.name

                inv = invoice.reversed_entry_id
                pre_gst = ''
                if inv.invoice_date:
                    if inv.invoice_date < gst_start_date:
                        pre_gst = 'Y'
                    else:
                        pre_gst = 'N'

                type = ''
                b2b = self.env['b2b.invoice'].search([('invoice_id', '=', inv.id)], limit=1)
                b2cl = self.env['b2cl.invoice'].search([('invoice_id', '=', inv.id)], limit=1)
                export = self.env['export.invoice'].search([('invoice_id', '=', inv.id)], limit=1)
                if b2b:
                    type = 'B2B'
                elif b2cl:
                    type = 'B2CL'
                elif export:
                    type = export.export_type
                else:
                    type = 'B2CS'

                if not invoice.partner_id.vat:
                    if invoice.move_type == 'in_refund':
                        document_type = 'C'
                    else:
                        document_type = 'D'
                    result = rec.get_lines(invoice)
                    for res in result:
                        vals = {'ur_type': type,
                                'voucher_id':invoice.id,
                                'voucher_date':invoice.invoice_date,
                                'document_type':document_type,
                                'invoice_number': invoice.invoice_origin,
                                'invoice_date': inv.invoice_date,
                                'reason':invoice.name,
                                'state_name':state_name,
                                'voucher_value': invoice.amount_total,
                                'rate': res,
                                'taxable_value': result[res],
                                'cess_amount':'',
                                'pre_gst':pre_gst,
                                'gst_return_id': rec.id,
                                }
                        self.env['cdnur.invoice'].create(vals)




            
# DOCS DATA
            rec._cr.execute("""
                SELECT
                    count(id),
                    min(invoice.name),
                    max(invoice.name)
                FROM
                    account_move invoice
                WHERE
                    company_id = %s AND
                    state != 'draft' AND
                    move_type = 'out_invoice' AND
                    invoice_date >= '%s' AND
                    invoice_date <= '%s' """ % (rec.company_id.id, rec.start_date, rec.end_date))
            invoice_result = rec._cr.fetchone()
            number_of_invoice = invoice_result[0] or 0
            from_invoice = invoice_result[1] or 0
            to_invoice = invoice_result[2] or 0

            out_invoice = all_invoices

            rec._cr.execute("""
                SELECT
                    count(id)
                FROM
                    account_move
                WHERE
                    company_id = %s AND
                    state = 'cancel' AND
                    move_type = 'out_invoice' AND
                    invoice_date >= '%s' AND
                    invoice_date <= '%s' """ % (rec.company_id.id, rec.start_date, rec.end_date))
            cancel_invoices = rec._cr.fetchone()
            number_of_cancel_invoice = cancel_invoices and cancel_invoices[0] or 0

            rec._cr.execute("""
                SELECT
                    count(id),
                    min(invoice.name),
                    max(invoice.name)
                FROM
                    account_move invoice
                WHERE
                    company_id = %s AND
                    state != 'draft' AND
                    move_type = 'out_refund' AND
                    invoice_date >= '%s' AND
                    invoice_date <= '%s' """ % (rec.company_id.id, rec.start_date, rec.end_date))
            note = rec._cr.fetchone()
            number_of_note = note[0] or 0
            from_note = note[1] or 0
            to_note = note[2] or 0

            rec._cr.execute("""
                SELECT
                    count(id)
                FROM
                    account_move
                WHERE
                    company_id = %s AND
                    state = 'cancel' AND
                    move_type = 'out_refund' AND
                    invoice_date >= '%s' AND
                    invoice_date <= '%s' """ % (rec.company_id.id, rec.start_date, rec.end_date))
            note_cancel = rec._cr.fetchone()
            number_of_cancel_note = note_cancel and note_cancel[0] or 0

            # total_cancel = number_of_cancel_note + number_of_cancel_invoice
            # total_invoice = number_of_invoice + number_of_note
            out_invoice = {
                'nature_of_document': 'Invoice for outward supply',
                'no_from': from_invoice,
                'no_to': to_invoice,
                'total': number_of_invoice,
                'cancelled': number_of_cancel_invoice,
                'gst_return_id': rec.id
                }
            self.env['docs.data'].create(out_invoice)
            debit_note = {
                'nature_of_document': 'Debit Note',
                'no_from': from_note,
                'no_to': to_note,
                'total': number_of_note,
                'cancelled': number_of_cancel_note,
                'gst_return_id': rec.id
            }
            self.env['docs.data'].create(debit_note)


    #       Exempt Data
            intra_state_registred_supply_non_gst = 0.0
            intra_state_unregistred_supply_non_gst = 0.0
            inter_state_registred_supply_non_gst = 0.0
            inter_state_unregistred_supply_non_gst = 0.0

            exempt_data = self.env['account.move'].search([('company_id', '=', rec.company_id.id),
                                                              ('state', 'not in', ('cancel', 'draft')),
                                                              ('move_type', '=', 'out_invoice')])
    #       NON GST SUPPLY
            for invoice in exempt_data:
                if invoice.partner_id.vat:
                    if invoice.partner_id.state_id == invoice.company_id.state_id:
                        for line in invoice.invoice_line_ids:
                            if not line.product_id:
                                intra_state_registred_supply_non_gst += line.price_subtotal
                    else:
                        for line in invoice.invoice_line_ids:
                            if not line.product_id:
                                inter_state_registred_supply_non_gst += line.price_subtotal

                else:
                    if invoice.partner_id.state_id == invoice.company_id.state_id:
                        for line in invoice.invoice_line_ids:
                            if not line.product_id:
                                intra_state_unregistred_supply_non_gst += line.price_subtotal
                    else:
                        for line in invoice.invoice_line_ids:
                            if not line.product_id:
                                inter_state_unregistred_supply_non_gst += line.price_subtotal


            inter_state_reg = {
                                'description': 'Inter-State supplies to registered persons',
                                'nil_rated_supplies': '',
                                'exempt_supplies': '',
                                'non_gst_supplies': inter_state_registred_supply_non_gst,
                                'gst_return_id': rec.id,
                                'supply_type': 'INTRB2B',
                                }
            self.env['exempt.data'].create(inter_state_reg)

            intra_state_reg = {
                                'description': 'Intra-State supplies to registered persons',
                                'nil_rated_supplies': '',
                                'exempt_supplies': '',
                                'non_gst_supplies': intra_state_registred_supply_non_gst,
                                'gst_return_id': rec.id,
                                'supply_type': 'INTRAB2B',
                                }
            self.env['exempt.data'].create(intra_state_reg)

            inter_state_un_reg = {
                                  'description': 'Intra-State supplies to Unregistered persons',
                                  'nil_rated_supplies': '',
                                  'exempt_supplies': '',
                                  'non_gst_supplies': inter_state_unregistred_supply_non_gst,
                                  'gst_return_id': rec.id,
                                  'supply_type': 'INTRB2C',
                                    }
            self.env['exempt.data'].create(inter_state_un_reg)

            intra_state_un_reg = {
                                    'description': 'Intra-State supplies to Unregistered persons',
                                    'nil_rated_supplies': '',
                                    'exempt_supplies': '',
                                    'non_gst_supplies': intra_state_unregistred_supply_non_gst,
                                    'gst_return_id': rec.id,
                                    'supply_type': 'INTRAB2C',
                                    }
            self.env['exempt.data'].create(intra_state_un_reg)
