from odoo import fields, models


class AccountItemLedger(models.TransientModel):
    """Item Ledger wizard - select item and date range."""

    _name = 'account.item.ledger'
    _description = 'Item Ledger'

    product_id = fields.Many2one(
        'product.product',
        string='Item / Product',
        help='Leave empty for all items.',
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: fields.Date.today(),
    )

    def action_print_pdf(self):
        """Generate Stock Item Ledger PDF report. Requires Item/Product to be selected."""
        self.ensure_one()
        if not self.product_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Product Required',
                    'message': 'Please select an Item / Product to generate the PDF report.',
                    'type': 'warning',
                    'sticky': False,
                },
            }
        return self.env.ref('arclight_account_custom.action_print_item_ledger').report_action(self)

    def get_report_lines(self):
        """Build Stock Item Ledger data for PDF using stock moves (incl. receipts & manufacturing)."""
        self.ensure_one()
        empty = {
            "report_lines": [],
            "product_name": "",
            "date_from_str": "",
            "date_to_str": "",
        }
        if not self.product_id:
            return empty

        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "=", "done"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("company_id", "=", self.env.company.id),
        ]
        move_lines = self.env["stock.move.line"].search(domain, order="date, id")

        rows = []
        running_qty = 0.0
        running_value = 0.0

        for line in move_lines:
            qty_in = line.qty_in or 0.0
            qty_out = line.qty_out or 0.0

            in_qty = qty_in
            out_qty = qty_out
            in_rate = in_value = 0.0
            out_rate = out_value = 0.0

            picking = line.picking_id
            move = line.move_id

            vch_type = "Stock Move"
            vch_no = ""
            partner_name = ""

            if picking:
                code = picking.picking_type_id.code
                if code == "incoming":
                    vch_type = "Receipt"
                elif code == "outgoing":
                    vch_type = "Delivery"
                elif code == "internal":
                    vch_type = "Internal Transfer"
                else:
                    vch_type = picking.picking_type_id.name or "Stock Move"
                vch_no = picking.name or ""
                partner_name = picking.partner_id.sudo().name if picking.partner_id else ""
            elif getattr(move, "production_id", False) or getattr(move, "raw_material_production_id", False):
                vch_type = "Manufacturing"
                vch_no = (
                    getattr(move.raw_material_production_id, "name", False)
                    or getattr(move.production_id, "name", False)
                    or move.reference
                    or ""
                )
            else:
                vch_no = move.reference or ""

            if in_qty:
                running_qty += in_qty
            if out_qty:
                running_qty -= out_qty
                if running_qty < 0:
                    running_qty = 0.0
                    running_value = 0.0

            close_qty = running_qty
            close_rate = (running_value / close_qty) if close_qty else 0.0

            date_str = line.date.strftime("%d-%b-%y") if line.date else ""

            rows.append(
                {
                    "date_str": date_str,
                    "particulars": partner_name or "",
                    "vch_type": vch_type,
                    "vch_no": vch_no,
                    "in_qty": in_qty,
                    "in_rate": in_rate,
                    "in_value": in_value,
                    "out_qty": out_qty,
                    "out_rate": out_rate,
                    "out_value": out_value,
                    "close_qty": close_qty,
                    "close_rate": close_rate,
                    "close_value": running_value,
                }
            )

        product_name = self.product_id.sudo().display_name if self.product_id else ""
        date_from_str = self.date_from.strftime("%d-%b-%y") if self.date_from else ""
        date_to_str = self.date_to.strftime("%d-%b-%y") if self.date_to else ""
        return {
            "report_lines": rows,
            "product_name": product_name,
            "date_from_str": date_from_str,
            "date_to_str": date_to_str,
        }

