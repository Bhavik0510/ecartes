# -*- coding: utf-8 -*-

from datetime import datetime, date, timedelta

from odoo import models, fields, api, _


class ContactDocument(models.Model):
    _name = 'contact.document'
    _description = 'Contact Documents'

    name = fields.Char(string='Document Number', required=True)
    document_name = fields.Many2one('contact.document.master', string='Document', required=True)
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    employee_ref = fields.Many2one('res.partner', copy=False)
    attachment_ids = fields.Many2many('ir.attachment', 'att_id', 'att_name', string="Attachment", copy=False)
    issue_date = fields.Date(string='Issue Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection(
        [
            ("running", "Running"),
            ("expired", "Expired"),
            ("renewed", "Renewed"),
        ],
        required=True,
        copy=False,
        default="running",
    )

    def mail_reminder(self):
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.expiry_date:
                exp_date = i.expiry_date - timedelta(days=7)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.employee_ref.name + ",<br>Your Document " + i.name + "is going to expire on " + \
                                   str(i.expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Document-%s Expired On %s') % (i.name, i.expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee_ref.work_email,
                    }
                    self.env['mail.mail'].create(main_content).send()

    @api.onchange('expiry_date')
    def check_expr_date(self):
        for each in self:
            exp_date = each.expiry_date
            if exp_date and exp_date < date.today():
                return {
                    'warning': {
                        'title': _('Document Expired.'),
                        'message': _("Your Document Is Already Expired.")
                    }
                }
