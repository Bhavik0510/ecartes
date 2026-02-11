from odoo import models, fields, api, _


class ContactDocumentSearch(models.Model):
    _inherit = 'res.partner'

    def _document_count(self):
        for each in self:
            document_ids = self.env['contact.document'].search([('employee_ref', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view_btn(self):
        self.ensure_one()
        domain = [
            ('employee_ref', '=', self.id)]
        ctx = dict(self._context)
        ctx.update({'default_employee_ref': self.id})
        return {
            'name': _('Documents'),
            'res_model': 'contact.document',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'view_id': False,
            'view_mode': 'list,form',
            'view_type': 'form',
            'limit': 80,
            'context': ctx
        }

    document_count = fields.Integer(compute='_document_count', string='# Documents')
