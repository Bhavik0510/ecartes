from odoo import fields, models


class AmcStatus(models.TransientModel):
    _name = 'amc.status'
    _description = 'Bulk Update AMC Status'

    state = fields.Selection([
        ('draft', 'New'),
        ('2beinvoice', 'To Be invoice'),
        ('invoiced', 'Invoiced'),
        ('under_amc', 'Under AMC'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('cancel', 'Cancelled'),
    ], required=True, string="State")

    def action_apply_state(self):
        active_ids = self.env.context.get('active_ids', [])
        amcs = self.env['amc.amc'].browse(active_ids)
        amcs.with_context(skip_amc_status_check=True).write({'state': self.state})
        return {'type': 'ir.actions.act_window_close'}
