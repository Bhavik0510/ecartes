from odoo import fields, models, api, _

class AccountMove(models.Model):
    _inherit = "account.move"

    tcs_amounts = fields.Float(string='TCS', compute='_customer_tcs_calculations')
    tcs_percentage = fields.Float(string='TCS %', related='partner_id.tax_id.amount')
    tds_percentage = fields.Float(string='TDS %', related='partner_id.tax_tds.amount')
    tds_amt = fields.Float(string='TDS', compute='tds_value_calculation')

    net_amounts = fields.Float(string=' Net Amount', compute='net_amount')
    net_val = fields.Float(string='Net Amount', compute='net_amt')
    amount_discount = fields.Monetary(string='Discount', store=True, readonly=True)

    def _customer_tcs_calculations(self):
        for i in self:
            if i.partner_id.tcs_applicable:
                val = ((i.amount_total * i.partner_id.tax_id.amount) / 100)
                i.tcs_amounts = val
            else:
                i.tcs_amounts = False

    def tds_value_calculation(self):
        if self.partner_id.tds_applicable:
            val = ((self.amount_untaxed * self.partner_id.tax_tds.amount) / 100)
            self.tds_amt = val
        else:
            self.tds_amt = False

    def net_amount(self):
        var = self.amount_total - self.tds_amt
        self.net_amounts = var

    def net_amt(self,var):
        self.net_val = self.amount_residual - var
        self.amount_residual = self.net_amounts

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type == 'in_invoice' and self.tds_amt > 0:
                move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                move_line_obj.create({
                    'move_id': move.id,
                    'account_id':self.env.ref('l10n_in.1_p11231').id,
                    'name': 'TDS Deduction',
                    'debit': self.tds_amt,
                    'credit': 0.0,
                    'exclude_from_invoice_tab': True,
                    'currency_id': move.currency_id.id,
                })
                for i in self.line_ids:
                    if i.account_id.id == self.env.ref('l10n_in.1_p11211').id:
                        if self.tds_amt:
                            i.credit += self.tds_amt

            if move.move_type == 'out_invoice' and self.tcs_amounts > 0:
                move_line_obj = self.env['account.move.line'].with_context(check_move_validity=False)
                move_line_obj.create({
                    'move_id': move.id,
                    'account_id': self.env.ref('l10n_in.1_p10041').id,
                    'name': 'TCS Collection',
                    'credit': self.tcs_amounts,
                    'debit': 0.0,
                    'exclude_from_invoice_tab': True,
                    'currency_id': move.currency_id.id,
                })
                for i in self.line_ids:
                    if i.account_id.id == self.env.ref('l10n_in.1_p10040').id:
                        if self.tcs_amounts:
                            i.debit += self.tcs_amounts
        return res

