from odoo import models, fields

class EmdRejectReason(models.TransientModel):
    _name = "emd.reject"
    _description = 'Emd Reject Reason'

    reject_reason = fields.Text('Reject Reason')
    def go_submit(self):
        if self._context.get('active_id'):
            emd = self.env['ecartes.emd'].browse(self._context.get('active_id'))
            if emd:
                emd.write(
                    {
                        'supervisor_id':False,
                        'manager_id':False,
                        'state':'rejected',
                        'reject_reason': self.reject_reason
                    })

