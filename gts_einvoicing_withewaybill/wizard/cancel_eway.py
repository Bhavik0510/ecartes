import json
import requests

from odoo import fields, models,api, _
from odoo.exceptions import UserError


class EwayBillCancel(models.TransientModel):
    _name = 'eway_bill.cancel'
    _description = "EwayBillCancel"


    eway_cancel_reason = fields.Char('Description')

    def cancel_eway_bill_no(self):
        active_id = self.env.context.get('active_id')
        order = self.env['account.move'].browse(active_id)
        einvoicing = self.env['einvoicing.configuration'].search([])
        delivery = self.env['stock.picking'].search([('origin', '=', order.invoice_origin)], limit=1)
        warehouse = delivery.picking_type_id.warehouse_id
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search([('company_id', '=', order.company_id.id)], limit=1)

        token = einvoicing.handle_einvoicing_auth_token()
        if not order.irn_no:
            raise UserError(_('Please Create E-Invoice First'))
        if not einvoicing:
            raise UserError(_('No Configurations details found in the system for E-Invoicing.'))
        if not warehouse.auth_token:
            raise UserError(_('Please Check Auth Token in warehouse configuration is Expired or Null.'))
        if not einvoicing.testing:
            raise UserError(_('Please Set Url Type in E-Invoicing Configuration.'))
        if not einvoicing.asp_id:
            raise UserError(_('Please Enter ASP-ID in E-Invoicing Configurations.'))
        if not einvoicing.asp_password:
            raise UserError(_('Please Enter ASP Password in E-Invoicing Configurations.'))
        if not warehouse.gst_no:
            raise UserError(_('Please Enter Registered GSTIN in warehouse Configurations.'))
        if not warehouse.user_password:
            raise UserError(_('Please Enter User Password in warehouse Configurations.'))
        if not warehouse.user_name:
            raise UserError(_('Please Enter User Name in Warehouse Configurations.'))
        if not order.eway_bill_no:
            raise UserError(_('Eway bill Number is not generated '))
        if not self.eway_cancel_reason:
            raise UserError(_('Please Enter Eway Bill Cancillation Reason.'))
        data = {
                "ewbNo": order.eway_bill_no,
                "cancelRsnCode": 2,
                "cancelRmrk": self.eway_cancel_reason
            }

        if einvoicing.testing == 't':
            url = 'https://gstsandbox.charteredinfo.com/ewaybillapi/dec/v1.03/ewayapi?action=CANEWB&aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&gstin=' + warehouse.gst_no + '&authtoken=' + warehouse.auth_token + '&username=' + warehouse.user_name
        if einvoicing.testing == 'p':
            url = 'https://einvapi.charteredinfo.com/v1.03/dec/ewayapi?action=CANEWB&aspid=' + einvoicing.asp_id + '&password=' + einvoicing.asp_password + '&gstin=' + warehouse.gst_no + '&authtoken=' + warehouse.auth_token + '&username=' + warehouse.user_name
        headers = {'Content-Type':'application/json;charset=utf-8'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        res = response.content
        res_dict = json.loads(res.decode('utf-8'))        
        if res_dict.get('status_cd') == '0':
            raise UserError(_(res_dict.get('error')))
        else:
            order.eway_cancel_date = res_dict.get('cancelDate')
            self.env.user.notify_info(message='Eway Bill Cancel Successfully !')
