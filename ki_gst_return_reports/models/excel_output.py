# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class GSTMonthlyStatementExcel(models.TransientModel):
    _name = 'monthly.gst.statement.excel'
    _description = 'Wizard to store the Excel output'
 
    xls_output = fields.Binary(string='Excel Output',
                               readonly=True
                               )
    name = fields.Char(string='File Name',
                        help='Save report as .xls format',
                        default='Salary Statement Monthly.xls',
                        )

class Output(models.TransientModel):
    _name = 'v.excel.output'
    _description = 'Excel Report Output'

    name = fields.Char('File Name', size=256, readonly=True)
    filename = fields.Binary('File to Download', readonly=True)
    extension = fields.Char('Extension', default='xls')

    @api.model
    def download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/document?model=%s&field=filename&id=%s&filename=%s.%s' % (self._name, self.id, self.name, self.extension),
            'target': 'self'
        }
        

class JsonOutput(models.TransientModel):
    _name = 'v.json.output'
    _description = 'Excel Report Output'

    name = fields.Char('File Name', size=256, readonly=True)
    filename = fields.Binary('File to Download', readonly=True)
    extension = fields.Char('Extension', default='JSON')

    @api.model
    def download(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/document?model=%s&field=filename&id=%s&filename=%s.%s' % (self._name, self.id, self.name, self.extension),
            'target': 'self'
        }