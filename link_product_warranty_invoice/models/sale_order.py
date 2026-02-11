from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero

class SaleOrder(models.Model):
    _inherit = "sale.order"

    warranty_ids = fields.Many2many(
        "product.warranty",
        string="Warranties",
        compute="_compute_warranty_ids",
    )

    warranty_count = fields.Integer(
        string="Warranty", compute="_compute_warranty_ids"
    )

    def _compute_warranty_ids(self):
        for sale in self:
            warranty = self.env['product.warranty'].search([('sale_id', '=', sale.id)]).ids
            sale.warranty_ids = warranty
            sale.warranty_count = len(warranty)

    def action_show_warranty(self):
        return {
            'name': _('Warranty'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'product.warranty',
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_stock_moves_link_invoice(self):
        moves_linked = self.env["stock.move"]
        to_invoice = self.qty_to_invoice
        for stock_move in self.move_ids.sorted(
            lambda m: (m.write_date, m.id), reverse=True
        ):
            if (
                stock_move.state != "done"
                or stock_move.scrapped
                or (
                    stock_move.location_dest_id.usage != "customer"
                    and (
                        stock_move.location_id.usage != "customer"
                        or not stock_move.to_refund
                    )
                )
            ):
                continue
            if not stock_move.invoice_line_ids:
                to_invoice -= (
                    stock_move.quantity
                    if not stock_move.to_refund
                    else -stock_move.quantity
                )
                moves_linked += stock_move
                continue
            elif float_is_zero(
                to_invoice, precision_rounding=self.product_uom.rounding
            ):
                break
            to_invoice -= (
                stock_move.quantity
                if not stock_move.to_refund
                else -stock_move.quantity
            )
            moves_linked += stock_move
        return moves_linked

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)
        stock_moves = self.get_stock_moves_link_invoice()
        # Invoice returned moves marked as to_refund
        if (
            float_compare(
                self.qty_to_invoice, 0.0, precision_rounding=self.currency_id.rounding
            )
            < 0
        ):
            stock_moves = stock_moves.filtered("to_refund")
        vals["stock_move_line_ids"] = [(4, m.id) for m in stock_moves]
        return vals
