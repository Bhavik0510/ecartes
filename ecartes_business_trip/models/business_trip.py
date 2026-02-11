from datetime import datetime

# from duplicity.errors import UserError
from odoo import models, fields, api, _
from odoo import exceptions

DEFAULT_MESSAGE = "Default message"

INFO = "info"
DEFAULT = "default"


class BusinessTrip(models.Model):
    _name = 'business.trip'
    _description = 'business trip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_id'

    name = fields.Char(string='Description')
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  default=lambda self: self.env.user.employee_id)
    request_date_from = fields.Date('Request Start Date')
    request_date_to = fields.Date('Request End Date')

    number_of_days = fields.Float(
        'Duration (Days)', compute='_compute_date')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', default='draft')
    leave_id = fields.Many2one(comodel_name="hr.leave", string="Leave")

    @api.depends('request_date_from', 'request_date_to')
    def _compute_date(self):
        for rec in self:
            if rec.request_date_from and rec.request_date_to:
                date = rec.request_date_to - rec.request_date_from
                rec.number_of_days = date.days + 1
            else:
                rec.number_of_days = 0

    def action_approve(self):
        self.state = 'validate1'
        self.activity_update()
        target = self.env.ref("ecartes_leaves.group_ecartes_leaves_management").users.partner_id
        message = "Business trip Request To Approve"
        self.notify_info(target=target, message=message)
        self.leave_id.state = 'validate1'
        # data=self.env["hr.leave"].search([('employee_id','=',self.employee_id.id),('state','=','confirm')],limit=1)
        # data.write({'state':'validate1'})

    def action_validate(self):
        self.state = 'validate'
        self.activity_update()
        self.leave_id.state = 'validate'
        # data = self.env["hr.leave"].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'validate1')],
        #                                    limit=1)
        # data.write({'state': 'validate'})

    def action_refuse(self):
        self.state = 'refuse'

        self.activity_update()
        # self.env.user.employee_id.manager_id
        target = self.env.ref("ecartes_leaves.group_ecartes_leaves_account").users.partner_id
        message = "Business trip Request refused"
        self.notify_info(target=target, message=message)
        data = self.env["hr.leave"].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),('state','=','validate1')],
                                           limit=1)
        data.write({'state': 'refuse'})

    def action_confirm(self):
        search_leave_type = self.env['hr.leave.type'].search([('is_business_trip', '=', True)], limit=1)
        if search_leave_type:
            create_business_trip = {
                'holiday_status_id': search_leave_type.id,
                'name': self.name,
                'employee_id': self.employee_id.id,
                'request_date_from': self.request_date_from,
                'request_date_to': self.request_date_to,
                'date_from': self.request_date_from,
                'date_to':self.request_date_to,
                'number_of_days': self.number_of_days,
                'duration_display': self.number_of_days,
                'state': self.state
            }
            self.leave_id = self.env['hr.leave'].create(create_business_trip)
            self.state = 'confirm'
            self.activity_update()
            target = self.env.user.employee_id.parent_id.user_id.partner_id
            message = "New Business Trip Request Generated"
            self.notify_info(target=target, message=message)
        else:
            raise exceptions.ValidationError("Please select business trip first")

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def _get_responsible_for_approval(self):
        self.ensure_one()
        responsible = None
        if self.state == 'confirm':
            responsible = self.env.user.employee_id.parent_id.user_id.ids or self.env.ref('ecartes_leaves.group_ecartes_leaves_management').users.ids
        if self.state == 'validate1':
            responsible = self.env.ref('ecartes_leaves.group_ecartes_leaves_management').users.ids

        return responsible

    def activity_update(self):
        for trip in self:
            note = _(
                'New Business trip Request created by %(user)s',
                user=trip.create_uid.name,
            )
            if trip.state == 'confirm':
                for users in trip.sudo()._get_responsible_for_approval():
                    trip.activity_schedule(
                        'ecartes_business_trip.mail_act_business_trip_user_manager_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            if trip.state == 'validate1':
                trip.activity_unlink(['ecartes_business_trip.mail_act_business_trip_user_manager_approval'])
                for users in trip.sudo()._get_responsible_for_approval():
                    trip.activity_schedule(
                        'ecartes_business_trip.mail_act_business_trip_approval',
                        note=note,
                        user_id=users or self.env.user.id)

            elif trip.state == 'validate':
                trip.activity_unlink(['ecartes_business_trip.mail_act_business_trip_approval', 'ecartes_business_trip.mail_act_business_trip_user_manager_approval'])

    def notify_info(
            self, message=None, title=None, sticky=False, target=None
    ):
        title = title or _("Information")
        self._notify_channel(INFO, message, title, sticky, target)

    def _notify_channel(self, type_message=None, message=None, title=None, sticky=False, target=None, ):
        if not target:
            target = self.env.ref("ecartes_leaves.group_ecartes_leaves_account").users.partner_id
        bus_message = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }
        for partner in target:
            self.env['bus.bus'].sudo()._sendone(partner.id, 'web.notify', bus_message)

    def view_leave(self):
        self.ensure_one()
        return {
            'name': _('Business Trip Leave'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.leave',
            'view_id': self.env.ref('hr_holidays.hr_leave_view_form').id,
            'target': 'current',
            'res_id': self.leave_id.id,
            'context': "{'create': False,'edit':False}"
        }