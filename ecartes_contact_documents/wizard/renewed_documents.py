# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api

from datetime import datetime, date, timedelta


class RenewedContactDocuments(models.TransientModel):
    _name = "renewed.documents"
    _description = "Renewed Contact Documents generate"

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

    name = fields.Char(string='Document Number', required=True, copy=False)
    document_name = fields.Many2one('contact.document.master', string='Document', required=True)
    description = fields.Text(string='Description', copy=False)
    expiry_date = fields.Date(string='Expiry Date', copy=False)
    employee_ref = fields.Many2one('res.partner', copy=False)
    attach_ids = fields.Many2many('ir.attachment', 'id', 'name', string="Attachment", copy=False)
    issue_date = fields.Date(string='Issue Date', default=fields.Date.context_today, copy=False)

    def renewed_method(self):
        active_id = self.env.context.get('active_ids')
        brws_id = self.env['contact.document'].browse(active_id)
        vals = {
            'attachment_ids': self.attach_ids,
            'issue_date': self.issue_date,
            'expiry_date': self.expiry_date}
        brws_id.write(vals)
        brws_id.state = 'renewed'

    @api.model
    def default_get(self, fields):
        result = super(RenewedContactDocuments, self).default_get(fields)
        active_id = self.env.context.get('active_ids')
        brws_id = self.env['contact.document'].browse(active_id)
        if active_id:
            result.update({
                'name': brws_id.name,
                'document_name': brws_id.document_name.id,
            })
        return result
