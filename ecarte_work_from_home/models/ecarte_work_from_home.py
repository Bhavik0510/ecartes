from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import werkzeug.urls
import random
from datetime import datetime, date, timedelta, time


def random_token():
    # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(20))

class EcarteWorkFromHome(models.Model):
    _name = 'ecarte.work.from.home'
    _description = 'Ecarte Work From Home'
    _rec_name = 'name'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    def _get_admin_user(self):
        admin = self.env['res.users'].sudo().search([]).filtered(lambda a:a.has_group('ecarte_work_from_home.group_wfh_hr'))
        return admin.id

    name = fields.Char(string="Name", required=True, copy=False, default='WFH Request', tracking=True)
    date_from = fields.Date(string="Date From", tracking=True)
    date_to = fields.Date(string="Date To", tracking=True)
    duration = fields.Integer(string="Duration", tracking=True,compute="compute_duration")
    description = fields.Char(string="Description", tracking=True)
    state = fields.Selection(string="Status", selection=[('draft', 'To Submit'), ('approve_by_manager', 'Approved By Manager'),('approved', 'Approved')],default="draft", tracking=True)
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    manager_id = fields.Many2one('hr.employee')
    user_id = fields.Many2one('res.users', string="User", related="employee_id.user_id")
    manager_user_id = fields.Many2one('res.users', string="Manager User", related="manager_id.user_id")
    admin_user_id = fields.Many2one('res.users', string="Admin User", default=_get_admin_user)
    approval_url = fields.Char(compute='_compute_approval_url', string='Approval Email URL')
    visible_manager_approve_btn = fields.Boolean(compute='_compute_visible_manager_approve_btn', string='Approval Btn')

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):
        for wfh in self.filtered('employee_id'):
            domain = [
                ('date_from', '<', wfh.date_to),
                ('date_to', '>', wfh.date_from),
                ('employee_id', '=', wfh.employee_id.id),
                ('id', '!=', wfh.id),
            ]
            wfh_ids = self.search_count(domain)
            if wfh_ids:
                raise ValidationError(
                    _('You can not set 2 WFH that overlaps on the same day for the same employee.'))

    def _compute_visible_manager_approve_btn(self):
        for rec in self:
            if self.env.user.id == rec.manager_user_id.id or self.env.user.id == rec.admin_user_id.id:
                rec.visible_manager_approve_btn=True
            else:
                rec.visible_manager_approve_btn=False



    def _compute_approval_url(self):
        result = self.sudo()._get_approval_url_for_action()
        for app in self:
            app.approval_url = result.get(app.id, False)

    def _get_approval_url_for_action(self, action=None, view_type=None, menu_id=None, res_id=None, model=None):

        res = dict.fromkeys(self.ids, False)
        for app in self:
            base_url = self.env.user.get_base_url()
            menu_id = self.env.ref('ecarte_work_from_home.work_from_home',False).id
            action_id = self.env.ref('ecarte_work_from_home.ecarte_work_from_home_action1',False).id
            approval_url = "/web/#id=%s&action=%s&model=ecarte.work.from.home&view_type=form&cids=1&menu_id=%s" % (self.id,action_id,menu_id)
            approval_url = werkzeug.urls.url_join(base_url, approval_url)
            res[app.id] = approval_url
        return res

    @api.model
    def default_get(self, fields):
        res = super(EcarteWorkFromHome, self).default_get(fields)
        res.update({
            'employee_id': self.env.user.employee_id.id,
            'manager_id': self.env.user.employee_id.parent_id.id,
        })
        return res

    def reset_to_draft(self):
        if self.state not in ['draft']:
            self.state = 'draft'

    def aprrove_by_manager(self):
        self.state = 'approve_by_manager'
        accountant =self.env.ref("ecarte_work_from_home.group_wfh_accounts").users.filtered(lambda x: x.email != False).mapped('email')
        wfh_mail_template = self.env.ref('ecarte_work_from_home.ecarte_work_from_home_tmp_approved_by_manager')
        wfh_mail_template.sudo().write({'email_to': ",".join(accountant)})
        wfh_mail_template.sudo().send_mail(self.id, force_send=True)

    def approve(self):
        self.state = 'approved'
        mail_data = {'subject': 'Work From Home Request approved !',
                     'body_html': ' Your request for work from home from '+str(self.date_from)+' to' + str(self.date_to)+ 'has been approved',
                     'email_to': self.employee_id.work_email,
                     }
        mail = self.env['mail.mail']
        mail_out = mail.sudo().create(mail_data)
        mail_out.sudo().send(mail_out)
        # if self.employee_id and self.employee_id.user_id:
        #     self.employee_id.user_id.write({
        #         'groups_id': [(4, self.env.ref('hr_attendance.group_hr_attendance').id)]
        #     })


    def _compute_manager_id(self):
        for rec in self:
            rec.manager_id = rec.employee_id.parent_id.id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'WFH Request') == 'WFH Request':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ecarte.work.from.home') or 'WFH Request'
        result = super(EcarteWorkFromHome, self).create(vals_list)
        manager = self.env.ref("ecarte_work_from_home.wfh_grp_manger").users.filtered(lambda x: x.email != False).mapped('email')
        for record in result:
            if record.get('manager_id'):
                wfh_mail_template = self.env.ref('ecarte_work_from_home.ecarte_work_from_home_tmp')
                wfh_mail_template.write({'email_to':", ".join(manager)})
                wfh_mail_template.sudo().send_mail(record.id,force_send=True)
            else:
                record.aprrove_by_manager()
        return result

    def daterange(self,date1, date2):
        for n in range(int((date2 - date1).days) + 1):
            yield date1 + timedelta(n)

    @api.onchange('date_from','date_to')
    def onchange_date_from_to(self):
        if self.date_to and self.date_from:
            if self.date_to < self.date_from:
                raise ValidationError(_('From Date should not be less than to Date'))
            if self.date_from < fields.Date.today():
                raise ValidationError(_("Can't create record before today date"))
            # weekdays = [5, 6]
            # count = 0
            # for dt in self.daterange(self.date_from, self.date_to):
            #     if dt.weekday() not in weekdays:  # to print only the weekdates
            #         count = count+1
            # self.duration = count

    @api.depends('date_from', 'date_to')
    def compute_duration(self):
        for rec in self:
            if rec.date_to and rec.date_from:
                if rec.date_to < rec.date_from:
                    rec.date_to = rec.date_from
                weekdays = [5, 6]
                count = 0
                for dt in rec.daterange(rec.date_from, rec.date_to):
                    if dt.weekday() not in weekdays:  # to print only the weekdates
                        count = count+1
                rec.duration = count
            else:
                rec.duration = 0

    def unlink(self):
        error_message = _('You cannot delete a record which is not in draft state')
        if self.user_has_groups('ecarte_work_from_home.group_wfh_hr'):
            return super(EcarteWorkFromHome, self).unlink()
        else:
            for rec in self:
                if rec.state not in ['draft']:
                    raise UserError(error_message)
                else:
                    return super(EcarteWorkFromHome, self).unlink()



