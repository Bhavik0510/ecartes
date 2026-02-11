from odoo import models ,fields ,api,exceptions, _
import werkzeug.urls
from datetime import datetime, timedelta,date

DEFAULT_MESSAGE = "Default message"

INFO = "info"
DEFAULT = "default"

class PbgDetails(models.Model):
    _name = "pbg.details"
    _rec_name = 'title'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'PBG Request'

    title = fields.Char("Title",tracking=True)
    beneficiary = fields.Many2one('res.partner',"Beneficiary",tracking=True)
    in_favour_of = fields.Char("In Favour Of",tracking=True)
    # deal_name_ID = fields.Many2one('crm.lead', string='Deal Name/ID',tracking=True)
    tender_deal_name_ID = fields.Many2one('tender.pipeline', string='Tender-Deal Name/ID',tracking=True)
    amount = fields.Float("BG Amount",tracking=True)
    currency_id = fields.Many2one('res.currency','Currency Type',tracking=True)

    payment_mode = fields.Selection([('dd','DD'),
                                ('online','Online'),
                                ('bg','BG'),
                                ('fdr','FDR')],
                                "Payment Mode",tracking=True)
    state = fields.Selection([("draft", "Draft"),
                              ("manager", "Submitted To Senior Management"),
                              ("approved", "Approved"),
                              ('issued', 'Issued'),
                              ('returned','Returned'),
                              ("rejected", "Rejected"),('canceled','Cancelled')],
                             default="draft",tracking=True)                            
    valid_till = fields.Date('PBG Expiry Date',tracking=True)
    due_date = fields.Date('Submission Deadline',tracking=True)
    beneficiary_address = fields.Text("Beneficiary Address",tracking=True)
    order_id = fields.Many2one('sale.order',string='Order Number',tracking=True)
    bank_details_attachments = fields.Binary("Draft Format",tracking=True)
    payable_at = fields.Char("Payable At", required=True, tracking=True)
    supervisor_id = fields.Many2one('res.users','Approved By Supervisor',tracking=True)
    issued_id = fields.Many2one('res.users', 'Issued By',tracking=True)
    manager_id = fields.Many2one('res.users','Approved By Manager',tracking=True)
    approval_url = fields.Char(compute='_compute_approval_url', string='Approval Email URL',tracking=True)
    ref_no = fields.Char(string="BG Number (Ref No)",tracking=True)
    issue_date = fields.Date(string="Issue Date", default=fields.Date.context_today, copy=False,tracking=True)
    pbg_amount = fields.Float(string="PBG Amount",tracking=True)
    reject_reason = fields.Text('Reject Reason',tracking=True)
    pbg_returned_date = fields.Date('PBG Returned Date',tracking=True)
    returned_amount = fields.Float('Returned Amount',tracking=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    claim_expiry_date = fields.Date(string="BG Claim Expiry date")
    per_of_margin = fields.Float(string="% of Margin")
    lien_on_fd = fields.Char(string="Lien on FD")
    bg_type = fields.Selection([('auto_renewal', 'Auto Renewal'), ('normal_bg', 'Normal BG')],
        string="BG Type")


    def approve_manager(self):
        account_group = self.env.ref('ecartes_pbg.group_ecartes_pbg_account')
        account_id=[]
        for rec in account_group.users:
                account_id.append(rec.partner_id.id)
        self.state = 'approved'
        self.write({'manager_id':self.env.user.id})
        self.activity_update()
        target = self.env.ref("ecartes_pbg.group_ecartes_pbg_account").users.partner_id
        message = "New PBG Issue Request Generated"
        self.notify_info(target=target, message=message)
        # temp_id = self.env.ref('ecartes_pbg.pbg_final_approved_mail_template')
        # temp_id.with_context(self.env.context).send_mail(self.id, force_send=True ,email_values={
        #        'recipient_ids': [(6,0, account_id)]})
        

    def send_to_manager(self):      
        manager_group = self.env.ref('ecartes_pbg.pbg_group_access_to_manager')

        manager_id=[]
        
        for rec in manager_group.users:
            manager_id.append(rec.partner_id.id)
        self.state ='manager'
        self.write({'supervisor_id':self.env.user.id}) 
        self.activity_update()
        target = self.env.ref("ecartes_pbg.pbg_group_access_to_manager").users.partner_id
        message = "New PBG Request Generated"
        self.notify_info(target=target, message=message)


       

    def send_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.write({'issued_id':False,'manager_id':False})


    def _compute_approval_url(self):
        result = self.sudo()._get_approval_url_for_action()
        for app in self:
            app.approval_url = result.get(app.id, False)

    def _get_approval_url_for_action(self, action=None, view_type=None, menu_id=None, res_id=None, model=None):
        res = dict.fromkeys(self.ids, False)
        for app in self:
            base_url = self.env.user.get_base_url()
            menu_id = self.env.ref('ecartes_pbg.menu_pbg_details',False).id
            action_id = self.env.ref('ecartes_pbg.action_pbg_details',False).id
            approval_url = "/web/#id=%s&action=%s&model=pbg.details&view_type=form&cids=1&menu_id=%s" % (self.id,action_id,menu_id)
            approval_url = werkzeug.urls.url_join(base_url, approval_url)
            res[app.id] = approval_url
        return res

    def send_to_reject(self):
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'reject.reason',
            'view_mode': 'form',
            'target': 'new'
        }   

    def pbg_validity_check_mail(self):          
        id = self.env['pbg.details'].search([])
        today_date = date.today()
        check_date = today_date - \
                 timedelta(days = 7)
        emailto = self.env.ref("ecartes_pbg.pbg_group_access_to_manager").users.mapped('email')
        for rec in id:
            if str(rec.valid_till) <= str(check_date):
                create_values = {
                'subject': 'Warning mail',
                'body_html': 'Your end cannot refund',
                'email_to': emailto,
                'auto_delete': False,
                }
                mail_id = self.env['mail.mail'].sudo().create(create_values)
                mail_id.sudo().send()        

    def set_to_cancel(self):
        self.state = 'canceled'


    def _get_responsible_for_approval(self):
        self.ensure_one()

        responsible = None

        if self.state == 'manager':
            responsible = self.env.ref("ecartes_pbg.pbg_group_access_to_manager").users.ids
        if self.state == 'approved':
            responsible = self.env.ref('ecartes_pbg.group_ecartes_pbg_account').users.ids

        return responsible    


    def activity_update(self):
        for pbg in self:
            note = _(
                'New PBG Request created by %(user)s',
                user=pbg.create_uid.name,
            )
            if pbg.state == 'manager':
                for users in pbg.sudo()._get_responsible_for_approval():
                    pbg.activity_schedule(
                        'ecartes_pbg.mail_act_pbg_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            elif pbg.state == 'approved':
                pbg.activity_unlink(['ecartes_pbg.mail_act_pbg_approval'])
                for users in pbg.sudo()._get_responsible_for_approval():
                    pbg.activity_schedule(
                        'ecartes_pbg.mail_act_pbg_second_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            elif pbg.state == 'issued':
                pbg.activity_unlink(['ecartes_pbg.mail_act_pbg_approval', 'ecartes_pbg.mail_act_pbg_second_approval'])


    def notify_info(
            self, message=None, title=None, sticky=False, target=None
    ):
        title = title or _("Information")
        self._notify_channel(INFO, message, title, sticky, target)


    def _notify_channel(self,type_message=None,message=None,title=None,sticky=False,target=None,):
        if not target:
            target = self.env.ref("ecartes_pbg.pbg_group_access_to_manager").users.partner_id
        bus_message = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }
        for partner in target:
            self.env['bus.bus'].sudo()._sendone(partner.id, 'web.notify', bus_message)
