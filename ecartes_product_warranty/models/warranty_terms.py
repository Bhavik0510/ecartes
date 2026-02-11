from odoo import api, fields, models

class WarrantyTerm(models.Model):
    _name = 'warranty.term'
    _rec_name = 'name'
    _description = 'Warranty Term'

    name = fields.Char(string="Warranty Term", required=True)
    active = fields.Boolean(default=True)
    warranty_by = fields.Selection(string="Warranty By", selection=[('year', 'Year'),('month', 'Month'), ('day', 'Days'), ], required=True, default="year" )
    total_no_of = fields.Integer(string="No. Of", required=True)
