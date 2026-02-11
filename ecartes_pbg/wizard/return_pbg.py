from odoo import models, fields


class ReturnPbg(models.TransientModel):
    _name = "return.pbg"
    _description = 'Return Pbg'

    pbg_returned_date = fields.Date('PBG Returned Date')
    returned_amount = fields.Float('Returned Amount')
    
    def go_submit(self):
        if self._context.get('active_id'):
            return_pbg = self.env['pbg.details'].browse(self._context.get('active_id'))
            if return_pbg:
                return_pbg.write(
                    {
                        'pbg_returned_date':self.pbg_returned_date,
                        'returned_amount': self.returned_amount,
                        'state':'returned'

                    })
