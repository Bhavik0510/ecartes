# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import datetime
import base64
from io import StringIO


class Gstr_Return(models.Model):
    _inherit = 'gstr.return'

    @api.model
    def get_lines_json(self, invoice):
        result = {}
        for line in invoice.invoice_line_ids:
            if not line.product_id.name == 'Down payment':
                tax_rate = 0
                cgst_amt = sgst_amt = igst_amt = 0.0
                for tax in line.tax_ids:
                    if tax.tax_group_id:
                        amount = line.price_subtotal
                        rate = tax.amount
                        if tax.tax_group_id.name == 'CGST':
                            cgst_amt = (amount * rate) / 100
                        if tax.tax_group_id.name== 'SGST':
                            sgst_amt = (amount * rate) / 100
                        if tax.tax_group_id.name == 'IGST':
                            igst_amt = (amount * rate) / 100
                        tax_rate = tax_rate + tax.amount
                if tax_rate not in result:
                    result[tax_rate] = {
                                        'txval': line.price_subtotal,
                                        'camt': cgst_amt,
                                        'samt': sgst_amt,
                                        'iamt': igst_amt
                                        }
                else:
                    result[tax_rate]['txval'] += line.price_subtotal
                    result[tax_rate]['camt'] += cgst_amt
                    result[tax_rate]['samt'] += sgst_amt
                    result[tax_rate]['iamt'] += igst_amt
        return result

    @api.model
    def get_b2cs_data(self, data):
        results = {}
       
        rate = 0
        cgst_amt = sgst_amt = igst_amt = 0.0
        rate = data.rate
        amount = data.taxable_value
        com_pos = str(self.company_id.state_id.l10n_in_tin)[:2]
        pos = str(data.state_name)[:2]
        if com_pos == pos:
            type = "INTRA"
            cgst_amt = (amount * (rate / 2)) / 100
            sgst_amt = (amount * (rate / 2)) / 100
        else:
            type = "INTER"
            igst_amt = (amount * rate) / 100
        results = {
                "sply_ty": type,
                "rt": rate,
                "typ": data.type,
                "etin": data.e_commerce_gstin or '',
                "pos": pos,
                'txval': amount,
                'camt': cgst_amt,
                'samt': sgst_amt,
                'iamt': igst_amt,
                "csamt": data.cess_amount
                }
        return results

    @api.model
    def gst_at_data(self, data):
        result = {}
        amount = 0
        rate = 0.0
        cgst_amt = sgst_amt = igst_amt = 0.0
        rate = data.rate
        amount = data.gross_advance_receipt
        com_pos = str(self.company_id.state_id.l10n_in_tin)[:2]
        pos = str(data.state_name)[:2]
        if com_pos == pos:
            rat = rate / 2.0
            cgst_amt = (float(amount) * rat) / 100.0
            sgst_amt = (float(amount) * rat) / 100.0
        else:
            igst_amt = (float(amount) * rate) / 100.0
        result = {
                  "rt": rate,
                  "ad_amt": amount,
                  "camt": cgst_amt,
                  "samt": sgst_amt,
                  "iamt": igst_amt,
                  "csamt": 0.0
                }
        return result


    def get_gst_json(self):
        com_pos = str(self.company_id.state_id.l10n_in_tin)[:2]
#         gstr = self.gst_return
        datee = self.start_date
        fp = str(datee.month) + str(datee.year)
        if datee.month < 10:
            fp = '0' + fp
        jsn = {
            "gstin": self.gstin,
            "fp": fp,
            "gt": 0.0,
            "cur_gt": 0.0,
        }
        
        gstr = self
        # B2B Data
        b2bs = gstr.b2b_invoice_ids
        if "b2b" not in jsn:
            jsn.update({"b2b": []})
        for data in b2bs:
            gst = {}
            invo = {}
            for idx, val in enumerate(jsn['b2b']):
                if data.gstin_number == val['ctin']:
                    gst = val
                    break
            if not gst:
                gst = {'ctin': data.gstin_number,
                       'inv': []}
                jsn["b2b"].append(gst)
            for indx, value in enumerate(gst['inv']):
                if data.invoice_id.name == value['inum']:
                    invo = value
                    break
            if not invo:
                pos = data.invoice_id.partner_id.state_id.l10n_in_tin
                invo = {
                        "inum": data.invoice_id.name,
                        "idt": data.invoice_date,
                        "val": data.invoice_value,
                        "pos": pos,
                        "rchrg": data.reverse_charge,
                        "etin":  '',
                        "inv_typ": "R",
                        "itms": []
                        }
                gst['inv'].append(invo)
                invoice = data.invoice_id
                result = self.get_lines_json(data.invoice_id)
                lst = []
                count = 0
                for res in result:
                    count += 1
                    itm_det = {
                        'rt': res,
                        'txval': result[res]['txval'],
                        'iamt': result[res]['iamt'],
                        'samt': result[res]['samt'],
                        'camt': result[res]['camt'],
                        'csamt': 0.0,
                        }
                    itms = {
                        'num': count,
                        'itm_det': itm_det
                        }
                    lst.append(itms)
                invo.update({'itms': lst})

        # B2CL Data
        b2cl = gstr.b2cl_invoice_ids
        if "b2cl" not in jsn:
            jsn.update({"b2cl": []})
        for data in b2cl:
            gst = {}
            invo = {}
            pos = data.invoice_id.partner_id.state_id.l10n_in_tin
            for idx, val in enumerate(jsn['b2cl']):
                if pos == val['pos']:
                    gst = val
                    break
            if not gst:
                gst = {'pos': pos,
                       'inv': []}
                jsn["b2cl"].append(gst)
            for indx, value in enumerate(gst['inv']):
                if data.invoice_id.number == value['inum']:
                    invo = value
                    break
            if not invo:
                pos = data.invoice_id.partner_id.state_id.l10n_in_tin
                invo = {
                        "inum": data.invoice_id.name,
                        "idt": data.invoice_date,
                        "val": data.invoice_value,
                        "etin": data.e_commerce_gstin or '',
                        "itms": []
                        }
                gst['inv'].append(invo)
                invoice = data.invoice_id
                result = self.get_lines_json(data.invoice_id)
                lst = []
                count = 0
                for res in result:
                    count += 1
                    itm_det = {
                        'rt': res,
                        'txval': result[res]['txval'],
                        'iamt': result[res]['iamt'],
                        'samt': result[res]['samt'],
                        'camt': result[res]['camt'],
                        'csamt': 0.0,
                        }
                    itms = {
                        'num': count,
                        'itm_det': itm_det
                        }
                    lst.append(itms)
                invo.update({'itms': lst})

        # B2CS Data
        b2cs = gstr.b2cs_invoice_ids
        if "b2cs" not in jsn:
            jsn.update({"b2cs": []})
        for data in b2cs:
            results = self.get_b2cs_data(data)
            jsn['b2cs'].append(results)

        # Export Data
        exp = gstr.export_invoice_ids
        if "exp" not in jsn:
            jsn.update({"exp": []})
        for data in exp:
            gst = {}
            invo = {}
            for idx, val in enumerate(jsn['exp']):
                if data.export_type == val['exp_typ']:
                    gst = val
                    break
            if not gst:
                gst = {'exp_typ': data.export_type,
                       'inv': []}
                jsn["exp"].append(gst)
            for indx, value in enumerate(gst['inv']):
                if data.invoice_id.name == value['inum']:
                    invo = value
                    break
            if not invo:
                invo = {
                        "inum": data.invoice_id.name,
                        "idt": data.invoice_date,
                        "val": data.invoice_value,
                        "sbpcode": '',
                        "sbnum": '',
                        "sbdt": '',
                        "itms": []
                        }
                gst['inv'].append(invo)
                invoice = data.invoice_id
                result = self.get_lines_json(data.invoice_id)
                lst = []
                count = 0
                for res in result:
                    itms = {
                        'rt': res,
                        'txval': result[res]['txval'],
                        'iamt': result[res]['iamt'],
                        }
                    lst.append(itms)
                invo.update({'itms': lst})

        # CDNR Data
        cdnr = gstr.cdnr_invoice_ids
        if "cdnr" not in jsn:
            jsn.update({"cdnr": []})
        for data in cdnr:
            gst = {}
            invo = {}
            for idx, val in enumerate(jsn['cdnr']):
                if data.gstin_number == val['ctin']:
                    gst = val
                    break
            if not gst:
                gst = {'ctin': data.gstin_number,
                       'nt': []}
                jsn["cdnr"].append(gst)
            for indx, value in enumerate(gst['nt']):
                if data.voucher_id.name == value['nt_num']:
                    invo = value
                    break
            if not invo:
                invo = {
                        "ntty": data.document_type,
                        "nt_num": data.voucher_id.name,
                        "nt_dt": data.voucher_id.invoice_date,
                        "p_gst": data.pre_gst,
                        "rsn": data.reason,
                        "inum": data.invoice_number,
                        "idt": data.invoice_date,
                        "val": data.voucher_value,
                        "itms": []
                        }
                gst['nt'].append(invo)
                invoice = data.voucher_id
                result = self.get_lines_json(data.voucher_id)
                lst = []
                count = 0
                for res in result:
                    count += 1
                    itm_det = {
                        'rt': res,
                        'txval': result[res]['txval'],
                        'iamt': result[res]['iamt'],
                        'samt': result[res]['samt'],
                        'camt': result[res]['camt'],
                        'csamt': 0.0,
                        }
                    itms = {
                        'num': count,
                        'itm_det': itm_det
                        }
                    lst.append(itms)
                invo.update({'itms': lst})

        # CDNUR Data

        cdnur = gstr.cdnur_invoice_ids
        if "cdnur" not in jsn:
            jsn.update({"cdnur": []})
        for data in cdnur:
            invo = {}
            for indx, value in enumerate(jsn['cdnur']):
                if data.voucher_id.name == value['nt_num']:
                    invo = value
                    break
            if not invo:
                invo = {
                        "typ": data.ur_type,
                        "ntty": data.document_type,
                        "nt_num": data.voucher_id.name,
                        "nt_dt": data.voucher_id.invoice_date,
                        "p_gst": data.pre_gst,
                        "rsn": data.reason,
                        "inum": data.invoice_number,
                        "idt": data.invoice_date,
                        "val": data.voucher_value,
                        "itms": []
                        }
                jsn['cdnur'].append(invo)
                result = self.get_lines_json(data.voucher_id)
                lst = []
                count = 0
                for res in result:
                    count += 1
                    itm_det = {
                        'rt': res,
                        'txval': result[res]['txval'],
                        'iamt': result[res]['iamt'],
                        'samt': result[res]['samt'],
                        'camt': result[res]['camt'],
                        'csamt': 0.0,
                        }
                    itms = {
                        'num': count,
                        'itm_det': itm_det
                        }
                    lst.append(itms)
                invo.update({'itms': lst})

        # AT Data
        at = gstr.advance_tax_ids
        if "at" not in jsn:
            jsn.update({"at": []})
        for data in at:
            gst = {}
            pos = str(data.state_name)[:2]
            for idx, val in enumerate(jsn['at']):
                if pos == val['pos']:
                    gst = val
                    break
            if not gst:
                if pos == com_pos:
                    type = 'INTRA'
                else:
                    type = 'INTER'
                gst = {
                        "pos": pos,
                        "sply_ty": type,
                        "itms": []
                        }
                jsn["at"].append(gst)
            result = self.gst_at_data(data)
            gst['itms'].append(result)

        # ADJUSTMENT Data
        adjstmnt = gstr.tax_adjust_ids
        if "txpd" not in jsn:
            jsn.update({"txpd": []})
        for data in adjstmnt:
            gst = {}
            pos = str(data.state_name)[:2]
            for idx, val in enumerate(jsn['txpd']):
                if pos == val['pos']:
                    gst = val
                    break
            if not gst:
                if pos == com_pos:
                    type = 'INTRA'
                else:
                    type = 'INTER'
                gst = {
                        "pos": pos,
                        "sply_ty": type,
                        "itms": []
                        }
                jsn["txpd"].append(gst)
            result = self.gst_at_data(data)
            gst['itms'].append(result)

        # Exempt Data

        nil = gstr.exempt_data_ids
        gst = {}
        if "nil" not in jsn:
            jsn.update({"nil": {}})
            gst = {'inv': []}
            jsn["nil"].update(gst)
        for data in nil:
            invo = {}
            invo = {
                    "sply_ty": data.supply_type,
                    "expt_amt": data.exempt_supplies,
                    "nil_amt": data.nil_rated_supplies,
                    "ngsup_amt": data.non_gst_supplies
                    }
            gst['inv'].append(invo)

        # HSN Data
        hsn = gstr.hsn_data_ids
        gst = {}
        if "hsn" not in jsn:
            jsn.update({"hsn": {}})
            gst = {'data': []}
            jsn["hsn"].update(gst)
        count = 0
        for data in hsn:
            count += 1
            invo = {}
            invo = {
                    "num": count,
                    "hsn_sc": data.hsn_code,
                    "desc": data.description,
                    "uqc": '',
                    "qty": data.total_quantity,
                    "val": data.total_value,
                    "txval": data.taxable_value,
                    'samt': data.sgst,
                    'camt': data.cgst,
                    "iamt": data.igst,
                    "csamt": data.cess_amount
                    }
            gst['data'].append(invo)

        # DOCS Data
        docs = gstr.docs_data_ids
        gst = {}
        if "docs_issue" not in jsn:
            jsn["doc_issue"] = {}
        if not gst:
            gst = {'doc_det': []}
            jsn["doc_issue"].update(gst)
        count = 0
        for data in docs:
            if data.total > 0:
                count += 1
                net = data.total - data.cancelled
                itm_det = {
                            "num": count,
                            "from": data.no_from,
                            "to": data.no_to,
                            "totnum": data.total,
                            "cancel": data.cancelled,
                            "net_issue": net
                            }
                itms = {
                    'doc_num': count,
                    'docs': itm_det
                    }
                gst['doc_det'].append(itms)

        d = json.dumps(jsn, indent=4, sort_keys=True, default=str)
        print("//c/c/c/c/c/c/c/c/c/")
        attach_id = self.env['v.json.output'].create({
            'name' : self.name,
            'filename': base64.b64encode(bytes(d, "utf-8"))
        })
        return attach_id.download()
