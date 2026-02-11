# -*- coding: utf-8 -*-
import werkzeug.urls
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta,date

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"

class EcartesEmd(models.Model):
    _name = 'ecartes.emd'
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec_name = 'deal_name_id'
    _description = 'EMD Request'
    
    # title = fields.Char('Title' ,tracking=True)
    state = fields.Selection([('draft','Draft'),
            ('approved_manager','Submitted To Senior Management'),('done','Approved'),('issued','Issued'),('returned','Returned'),
            ('rejected','Rejected'),('canceled','Cancelled')],default='draft',tracking=True)
    beneficiary_id = fields.Many2one('res.partner','Beneficiary',tracking=True)
    in_favour_of = fields.Char('In Favour Of',tracking=True)
    deal_name_id = fields.Many2one('tender.pipeline','Deal/Tender Name',tracking=True)
    amount = fields.Float('Amount',tracking=True)
    payment_mode = fields.Selection([('dd','DD'),('online','Online'),('bg','BG'),('fdr','FDR')],tracking=True)
    valid_till = fields.Date('EMD Expiry Date',tracking=True)
    due_date =fields.Date('Submission Deadline',tracking=True)
    bank_details = fields.Text('Bank Details',tracking=True)
    bank_details_attachments = fields.Binary('Bank Details Attachments',tracking=True)
    payable_at = fields.Char('Payable At', required=True, tracking=True)
    emd_returned_date = fields.Date('EMD Returned Date',tracking=True)
    returned_amount = fields.Float('Returned Amount',tracking=True)
    section = fields.Char('Sections',tracking=True)
    has_been_published = fields.Selection([('yes','Yes'),('no','No')],tracking=True)
    action = fields.Char('Action',tracking=True)
    business_process_name = fields.Char('Business Process Name',tracking=True)
    current_status_date = fields.Date('Current Status Date',tracking=True)
    current_status = fields.Char('Current Status',tracking=True)
    supervisor_id = fields.Many2one('res.users','Approved By Supervisor',tracking=True)
    issued_id = fields.Many2one('res.users', 'Issued By',tracking=True)
    manager_id = fields.Many2one('res.users','Approved By Manager',tracking=True)
    approval_url = fields.Char(compute='_compute_approval_url', string='Approval Email URL',tracking=True)
    ref_no = fields.Char(string="Ref No",tracking=True)
    issue_date = fields.Date(string="Issue Date", default=fields.Date.context_today, copy=False,tracking=True)
    emd_amount = fields.Float(string="Issued EMD Amount",tracking=True)
    reject_reason = fields.Text('Reject Reason',tracking=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    beneficiary_name = fields.Char(string="Beneficiary Name")
    customer_email = fields.Char(string="Customer E-mail Address")
    contact_number = fields.Char(string="Contact Number")
    tender_ref_no = fields.Char(string="Tender Ref No")
    tender_id = fields.Char(string="Tender ID")
    dd_no = fields.Char(string="DD Number")
    neft_rtgs_ref_no = fields.Char(string="NEFT/RTGD Ref No")
    paid_by_bank = fields.Char(string="Paid By Bank")

    def approve_manager(self):
        account_group = self.env.ref('ecartes_emd.group_ecartes_emd_account')
        account_id=[]
        for rec in account_group.users:
                account_id.append(rec.partner_id.id)
        self.state = 'done'
        self.write({'manager_id':self.env.user.id})
        self.activity_update()
        target = self.env.ref("ecartes_emd.group_ecartes_emd_account").users.partner_id
        message = "New Emd Issue Request Generated"
        self.notify_info(target=target, message=message)
        # temp_id = self.env.ref('ecartes_emd.final_approved_mail_template')
        # temp_id.with_context(self.env.context).send_mail(self.id, force_send=True ,email_values={
        #        'recipient_ids': [(6,0, account_id)]})

    def send_to_manager(self):      
        manager_group = self.env.ref('ecartes_emd.group_ecartes_emd_manager')

        manager_id=[]
        for rec in manager_group.users:
                manager_id.append(rec.partner_id.id)
        self.state ='approved_manager'
        self.write({'supervisor_id':self.env.user.id})
        self.activity_update()
        target = self.env.ref("ecartes_emd.group_ecartes_emd_manager").users.partner_id
        message = "New Emd Request Generated"
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
            menu_id = self.env.ref('ecartes_emd.menu_ecartes_emd_details_user',False).id
            action_id = self.env.ref('ecartes_emd.ecartes_emd_action',False).id
            approval_url = "/web/#id=%s&action=%s&model=ecartes.emd&view_type=form&cids=1&menu_id=%s" % (self.id,action_id,menu_id)
            approval_url = werkzeug.urls.url_join(base_url, approval_url)
            res[app.id] = approval_url
        return res


    def send_to_reject(self):
            return {
                'name': 'Reject Reason',
                'type': 'ir.actions.act_window',
                'res_model': 'emd.reject',
                'view_mode': 'form',
                'target': 'new'
            }

    def emd_validity_check_mail(self):          
        id = self.env['ecartes.emd'].search([])
        today_date = date.today()
        check_date = today_date - \
                 timedelta(days = 7)
        emailto = self.env.ref("ecartes_emd.group_ecartes_emd_manager").users.mapped('email')

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

        if self.state == 'approved_manager':
            responsible = self.env.ref("ecartes_emd.group_ecartes_emd_manager").users.ids
        if self.state == 'done':
            responsible = self.env.ref('ecartes_emd.group_ecartes_emd_account').users.ids

        return responsible
    def activity_update(self):
        for emd in self:
            note = _(
                'New Emd Request created by %(user)s',
                user=emd.create_uid.name,
            )
            if emd.state == 'approved_manager':
                for users in emd.sudo()._get_responsible_for_approval():
                    emd.activity_schedule(
                        'ecartes_emd.mail_act_emd_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            elif emd.state == 'done':
                emd.activity_unlink(['ecartes_emd.mail_act_emd_approval'])
                for users in emd.sudo()._get_responsible_for_approval():
                    emd.activity_schedule(
                        'ecartes_emd.mail_act_emd_second_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            elif emd.state == 'issued':
                emd.activity_unlink(['ecartes_emd.mail_act_emd_approval', 'ecartes_emd.mail_act_emd_second_approval'])

    def notify_info(
            self, message=None, title=None, sticky=False, target=None
    ):
        title = title or _("Information")
        self._notify_channel(INFO, message, title, sticky, target)


    def _notify_channel(self,type_message=None,message=None,title=None,sticky=False,target=None,):
        if not target:
            target = self.env.ref("ecartes_emd.group_ecartes_emd_manager").users.partner_id
        bus_message = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }
        # notifications = [[partner, "web.notify", [bus_message]] for partner in target]
        # self.env["bus.bus"].sudo()._sendmany(notifications)
        for partner in target:
            self.env['bus.bus'].sudo()._sendone(partner.id, 'web.notify', bus_message)