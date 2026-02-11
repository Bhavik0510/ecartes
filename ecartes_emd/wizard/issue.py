# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api

from datetime import datetime, date, timedelta


class IssueEmd(models.TransientModel):
    _name = "issue.emd"
    _description = "Issue Employee generate"

    ref_no = fields.Char(string="Ref No", required=True, )
    issue_date = fields.Date(string="Issue Date", required=True, default=fields.Date.context_today, copy=False)
    emd_amount = fields.Float(string="EMD Amount",  required=True, )
    dd_no = fields.Char(string="DD Number")
    neft_rtgs_ref_no = fields.Char(string="NEFT/RTGD Ref No")
    paid_by_bank = fields.Char(string="Paid By Bank")


    def Issue_method(self):
        active_id = self.env.context.get('active_ids')
        brws_id = self.env['ecartes.emd'].browse(active_id)
        vals = {'ref_no': self.ref_no,
                'issue_date': self.issue_date,
                'emd_amount': self.emd_amount,
                'dd_no': self.dd_no,
                'neft_rtgs_ref_no': self.neft_rtgs_ref_no,
                'paid_by_bank': self.paid_by_bank}
        brws_id.write(vals)
        brws_id.state = 'issued'
        brws_id.write({'issued_id': self.env.user.id})
        brws_id.activity_update()
