from odoo import api, fields, models

class AmcVisitor(models.Model):
    _name = 'amc.visitor'
    _description = "AMC Visitor"

    amc_id = fields.Many2one('amc.amc')
    engineer_id = fields.Many2one('hr.employee', 'Engineer')
    document_ids = fields.Many2many('ir.attachment')
    visit_date = fields.Date('Visit Date')

