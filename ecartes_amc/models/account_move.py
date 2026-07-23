from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Keep this field in ecartes_amc as well so AMC views/actions never crash
    # even if another module that also defines it is not loaded in the registry.
    is_amc_invoice = fields.Boolean(
        string="AMC Invoice",
        default=False,
        copy=False,
    )
    amc_id = fields.Many2one(comodel_name="amc.amc", string="AMC")

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        SaleOrder = self.env['sale.order'].sudo()
        for move in moves:
            if move.move_type != 'out_invoice':
                continue
            order = move.order_id
            if not order and move.invoice_origin:
                order = SaleOrder.search([
                    ('name', '=', move.invoice_origin),
                    ('company_id', '=', move.company_id.id),
                ], limit=1)
            if not order or not order.amc_id:
                continue
            amc = order.amc_id
            amc.with_context(skip_amc_status_check=True).write({
                'invoice_ids': [(4, move.id)],
                'invoice_id': move.id,
                'state': 'invoiced',
            })
            move.write({
                'amc_id': amc.id,
                'is_amc_invoice': True,
            })
        return moves
