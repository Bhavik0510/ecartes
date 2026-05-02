from odoo import models, fields, api, _

class Manufacture(models.Model):
    _inherit = "mrp.production"
    _order = 'date_start desc'

