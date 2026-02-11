from odoo import api, fields, models

class AmcTerm(models.Model):
    _name = 'amc.term'
    _rec_name = 'name'
    _description = 'Amc Term'

    name = fields.Char(string="AMC Term", required=True)
    active = fields.Boolean(default=True)
    amc_by = fields.Selection(string="AMC By", selection=[('year', 'Year'),('month', 'Month'), ('day', 'Days'), ], required=True, default="year" )
    total_no_of = fields.Integer(string="No. Of", required=True)
