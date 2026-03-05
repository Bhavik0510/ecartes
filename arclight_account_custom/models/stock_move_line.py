from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    qty_in = fields.Float(
        string="Quantity In",
        compute="_compute_qty_in_out",
        store=True,
    )
    qty_out = fields.Float(
        string="Quantity Out",
        compute="_compute_qty_in_out",
        store=True,
    )

    @api.depends("quantity", "location_id.usage", "location_dest_id.usage")
    def _compute_qty_in_out(self):
        for line in self:
            qty_in = qty_out = 0.0
            qty = line.quantity or 0.0
            if qty:
                src_usage = line.location_id.usage
                dst_usage = line.location_dest_id.usage
                if dst_usage == "internal" and src_usage != "internal":
                    qty_in = qty
                elif src_usage == "internal" and dst_usage != "internal":
                    qty_out = qty
                elif src_usage == "internal" and dst_usage == "internal":
                    qty_out = qty
            line.qty_in = qty_in
            line.qty_out = qty_out

