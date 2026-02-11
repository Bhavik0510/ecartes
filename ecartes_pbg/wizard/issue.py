# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api

from datetime import datetime, date, timedelta


class IssueEmd(models.TransientModel):
    _name = "issue.pbg"
    _description = "Issue Employee generate"

    ref_no = fields.Char(string="BG No", required=True, )
    issue_date = fields.Date(string="Issue Date", required=True, default=fields.Date.context_today, copy=False)
    pbg_amount = fields.Float(string="PBG Amount",  required=True, )
    claim_expiry_date = fields.Date(string="BG Claim Expiry date")
    per_of_margin = fields.Float(string="% of Margin")
    lien_on_fd = fields.Char(string="Lien on FD")
    bg_type = fields.Selection([('auto_renewal', 'Auto Renewal'), ('normal_bg', 'Normal BG')],
        string="BG Type")

    def Issue_method(self):
        active_id = self.env.context.get('active_ids')
        brws_id = self.env['pbg.details'].browse(active_id)
        vals = {'ref_no': self.ref_no,
                'issue_date': self.issue_date,
                'pbg_amount': self.pbg_amount,
                'claim_expiry_date': self.claim_expiry_date,
                'per_of_margin': self.per_of_margin,
                'lien_on_fd': self.lien_on_fd,
                'bg_type': self.bg_type}
        brws_id.write(vals)
        brws_id.state = 'issued'
        brws_id.write({'issued_id': self.env.user.id})
        brws_id.activity_update()