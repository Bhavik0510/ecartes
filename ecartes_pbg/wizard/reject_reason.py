from odoo import models, fields


class RejectReason(models.TransientModel):
    _name = "reject.reason"
    _description = 'Reject Reason'

    reject_reason = fields.Text('Reject Reason')
    
    def go_submit(self):
        if self._context.get('active_id'):
            pbg = self.env['pbg.details'].browse(self._context.get('active_id'))
            if pbg:
                pbg.write(
                    {
                        'supervisor_id':False,
                        'manager_id':False,
                        'state':'rejected',
                        'reject_reason': self.reject_reason
                    })
