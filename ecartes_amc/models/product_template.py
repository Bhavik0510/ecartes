from odoo import api, fields, models


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_under_amc = fields.Boolean(string="Under AMC")
    allow_renewal = fields.Boolean(string="Allow Renewal")
