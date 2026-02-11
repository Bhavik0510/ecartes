from odoo import api, fields, models,_
from datetime import datetime
from dateutil import relativedelta

class AmdRenew(models.TransientModel):
    _name = "amc.renew"
    _description = 'Amd Renew'

    amc_id = fields.Many2one(comodel_name="amc.amc", string="AMC")


    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        )

    amc_start_date = fields.Date(string="AMC Start Date", default=datetime.today())
    amc_end_date = fields.Date(string="AMC End Date")
    amc_term_id = fields.Many2one(comodel_name="amc.term", string="AMC Term")

    line_ids = fields.One2many(comodel_name="amc.line", inverse_name="amc_id")

    # amc_id = fields.Many2one(comodel_name="amc.amc")

    renewal_amt = fields.Float(string="Renewal Amount")
    renewal_user_id = fields.Many2one('res.users', string="Renewal By", default=lambda self: self.env.user,
                                     )


    @api.onchange('amc_term_id')
    def onchnage_amc_term(self):
        if self.amc_term_id.amc_by == 'year':
            end_date = self.amc_start_date + relativedelta.relativedelta(years=self.amc_term_id.total_no_of)
            self.amc_end_date = end_date
        if self.amc_term_id.amc_by == 'month':
            end_date = self.amc_start_date + relativedelta.relativedelta(months=self.amc_term_id.total_no_of)
            self.amc_end_date = end_date
        if self.amc_term_id.amc_by == 'day':
            end_date = self.amc_start_date + relativedelta.relativedelta(days=self.amc_term_id.total_no_of)
            self.amc_end_date = end_date

    def btn_save(self):
        self.amc_id.write({
            'amc_start_date': self.amc_start_date,
            'amc_end_date': self.amc_end_date,
            'amc_term_id': self.amc_term_id.id,
            'amc_type': 'paid',
            'amc_amt': self.renewal_amt,
            'is_renewed': True,
            'renew_date': datetime.today().date(),
            'state': '2beinvoice',
            'renewal_user_id': self.renewal_user_id.id,

        })
