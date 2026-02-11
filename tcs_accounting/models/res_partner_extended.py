from odoo import api, fields, models,_

class ResPartnerExtended(models.Model):
    _inherit = 'res.partner'

    tcs_percentage = fields.Float(string='TCS %')
    tcs_applicable = fields.Boolean(string='TCS Applicable', default=False)

    tds_applicable = fields.Boolean(string='TDS Applicable', default=False)
    tds_percentage = fields.Float(string='TDS %', )
    tds_sec = fields.Many2one('tds.accounting', string='TDS section')

    tax_id = fields.Many2one('account.tax', string='Tax Tcs')
    tax_tds = fields.Many2one('account.tax', string='Tax Tds')
