from collections import defaultdict

from odoo import _, api, fields, models


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    is_warranty_created = fields.Boolean(
        string="Warranty Created",
        default=False,
        copy=False,
    )

    def add_warranty(self):
        for rec in self:
            # Check if warranty already exists for this invoice
            existing_warranty = self.env["product.warranty"].search([("invoice_id", "=", rec.id)], limit=1)
            if existing_warranty:
                return rec.action_show_warranty()

            line_cmds = []
            all_lots = []
            first_product = False
            first_warranty_term = False

            sale_order = rec.order_id
            if not sale_order and rec.invoice_origin:
                sale_order = self.env['sale.order'].sudo().search([
                    ('name', '=', rec.invoice_origin),
                    ('company_id', '=', rec.company_id.id)
                ], limit=1)
            if not sale_order and hasattr(rec, 'invoice_line_ids'):
                sale_orders = rec.invoice_line_ids.mapped('sale_line_ids.order_id')
                if sale_orders:
                    sale_order = sale_orders[0]

            for lines in rec.invoice_line_ids:
                if lines.product_id.is_under_warranty:
                    if not first_product:
                        first_product = lines.product_id
                    if not first_warranty_term and lines.product_id.warranty_term_id:
                        first_warranty_term = lines.product_id.warranty_term_id

                    if lines.product_id.tracking in ["serial", "lot"]:
                        lots = lines.prod_lot_ids
                        # Fallback 1: via sale order lines linked to invoice line
                        if not lots and hasattr(lines, 'sale_line_ids') and lines.sale_line_ids:
                            lots = lines.sale_line_ids.mapped('move_ids').filtered(
                                lambda m: m.state == 'done' and not m.scrapped
                            ).mapped('move_line_ids').filtered(
                                lambda ml: ml.state == 'done' and ml.lot_id and ml.product_id == lines.product_id
                            ).mapped('lot_id')
                        # Fallback 2: via sale_order pickings
                        if not lots and sale_order:
                            lots = sale_order.picking_ids.filtered(
                                lambda p: p.state == 'done'
                            ).mapped('move_line_ids').filtered(
                                lambda ml: ml.state == 'done' and ml.lot_id and ml.product_id == lines.product_id
                            ).mapped('lot_id')
                        # Fallback 3: via invoice name or invoice_origin picking
                        if not lots:
                            origins = [orig for orig in [rec.name, rec.invoice_origin, sale_order.name if sale_order else False] if orig]
                            if origins:
                                lots = self.env['stock.move.line'].search([
                                    ('picking_id.origin', 'in', origins),
                                    ('product_id', '=', lines.product_id.id),
                                    ('lot_id', '!=', False),
                                    ('state', '=', 'done')
                                ]).mapped('lot_id')

                        if lots and all_lots:
                            unused_lots = lots.filtered(lambda l: l.id not in all_lots)
                            if unused_lots:
                                lots = unused_lots

                        if lots:
                            all_lots.extend(lots.ids)
                            line_cmds.append((0, 0, {
                                "product_id": lines.product_id.id,
                                "lot_ids": [(6, 0, lots.ids)],
                                "product_qty": lines.quantity,
                                "company_id": rec.company_id.id,
                                "tracking": lines.product_id.tracking,
                            }))
                        else:
                            line_cmds.append((0, 0, {
                                "product_id": lines.product_id.id,
                                "lot_ids": False,
                                "product_qty": lines.quantity,
                                "company_id": rec.company_id.id,
                                "tracking": lines.product_id.tracking,
                            }))
                    else:
                        line_cmds.append((0, 0, {
                            "product_id": lines.product_id.id,
                            "lot_ids": False,
                            "product_qty": lines.quantity,
                            "company_id": rec.company_id.id,
                            "tracking": lines.product_id.tracking or "none",
                        }))

            # Old code: created separate warranty per product line and serial number
            # for lines in rec.invoice_line_ids:
            #     if lines.product_id.is_under_warranty:
            #         if lines.product_id.tracking in ["serial", "lot"]:
            #             for lot in lines.prod_lot_ids:
            #                 vals = {
            #                     "invoice_id": self.id,
            #                     "partner_id": self.partner_id.id,
            #                     "warranty_type": "free",
            #                     "warranty_term_id": lines.product_id.warranty_term_id.id,
            #                     "warranty_start_date": self.invoice_date,
            #                     "product_id": lines.product_id.id,
            #                     "lot_ids": [(4, lot.id)],
            #                     "sale_order_id": rec.order_id.id if rec.order_id else False,
            #                 }
            #                 warranty = self.env["product.warranty"].create(vals)
            #                 warranty.onchnage_warranty_term()
            #                 warranty.confirm_warranty()
            #         else:
            #             vals = {
            #                 "invoice_id": self.id,
            #                 "partner_id": self.partner_id.id,
            #                 "warranty_type": "free",
            #                 "warranty_term_id": lines.product_id.warranty_term_id.id,
            #                 "warranty_start_date": self.invoice_date,
            #                 "product_id": lines.product_id.id,
            #                 "product_qty": lines.quantity,
            #                 "sale_order_id": rec.order_id.id if rec.order_id else False,
            #             }
            #             warranty = self.env["product.warranty"].create(vals)
            #             warranty.onchnage_warranty_term()
            #             warranty.confirm_warranty()

            if line_cmds:
                if not first_warranty_term:
                    first_warranty_term = self.env['warranty.term'].search([
                        ('warranty_by', '=', 'year'),
                        ('total_no_of', '=', 1)
                    ], limit=1)

                vals = {
                    "invoice_id": rec.id,
                    "partner_id": rec.partner_id.id,
                    "company_id": rec.company_id.id,
                    "warranty_type": "free",
                    "warranty_term_id": first_warranty_term.id if first_warranty_term else False,
                    "warranty_start_date": rec.invoice_date or fields.Date.today(),
                    "product_id": first_product.id if first_product else False,
                    "lot_ids": [(6, 0, list(dict.fromkeys(all_lots)))] if all_lots else False,
                    "product_qty": sum(cmd[2]["product_qty"] for cmd in line_cmds),
                    "sale_order_id": sale_order.id if sale_order else False,
                    "sale_order_ref": (sale_order.client_order_ref or rec.invoice_origin) if sale_order else (rec.invoice_origin or False),
                    "line_ids": line_cmds,
                }
                warranty = self.env["product.warranty"].create(vals)
                warranty.onchnage_warranty_term()
                warranty.confirm_warranty()
                rec.is_warranty_created = True

            rec.invalidate_recordset(["warranty_count"])

    def action_show_warranty(self):
        self.ensure_one()
        warranties = self.env["product.warranty"].search([("invoice_id", "=", self.id)])
        action = {
            "name": _("Warranty"),
            "type": "ir.actions.act_window",
            "res_model": "product.warranty",
            "context": "{'create': False}",
        }
        if len(warranties) == 1:
            action["view_mode"] = "form"
            action["res_id"] = warranties.id
        else:
            action["view_mode"] = "list,form"
            action["domain"] = [("invoice_id", "=", self.id)]
        return action


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    stock_move_line_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="stock_move_invoice_line_rel",
        column1="invoice_line_id",
        column2="move_id",
        string="Related Stock Moves",
        readonly=True,
        copy=False,
    )

    prod_lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        compute="_compute_prod_lots",
        string="Production Lots",
    )

    @api.depends("stock_move_line_ids")
    def _compute_prod_lots(self):
        for line in self:
            line.prod_lot_ids = line.mapped(
                "stock_move_line_ids.move_line_ids.lot_id"
            )

    def lots_grouped_by_quantity(self):
        lot_dict = defaultdict(float)
        for sml in self.mapped("stock_move_line_ids.move_line_ids"):
            lot_dict[sml.lot_id.name] += sml.qty_done
        return lot_dict

    def copy_data(self, default=None):
        res_list = super().copy_data(default=default)
        if self.env.context.get("force_copy_stock_moves"):
            for line, res in zip(self, res_list):
                if "stock_move_line_ids" not in res:
                    res["stock_move_line_ids"] = [(6, 0, line.stock_move_line_ids.ids)]
        return res_list
