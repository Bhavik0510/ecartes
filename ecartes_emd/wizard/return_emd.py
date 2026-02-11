from odoo import models, fields


class ReturnEmd(models.TransientModel):
    _name = "return.emd"
    _description = 'Return Emd'

    emd_returned_date = fields.Date('EMD Returned Date')
    returned_amount = fields.Float('Returned Amount')
    
    def go_submit(self):
        if self._context.get('active_id'):
            return_emd = self.env['ecartes.emd'].browse(self._context.get('active_id'))
            if return_emd:
                return_emd.write(
                    {
                        'emd_returned_date':self.emd_returned_date,
                        'returned_amount': self.returned_amount,
                        'state':'returned'

                    })
