from odoo import api, fields, models,_
from collections import defaultdict


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    warranty_ids = fields.Many2many(
        comodel_name="product.warranty",
        string="Warranties",
        compute="_compute_warranty_ids",
    )

    warranty_count = fields.Integer(
        string="No of Warranty", compute="_compute_warranty_ids"
    )

    is_warranty_created = fields.Boolean(string="Create Warranty?")

    def _compute_warranty_ids(self):
        for invoice in self:
            warranty = self.env['product.warranty'].search([('invoice_id','=',invoice.id)]).ids
            invoice.warranty_ids = warranty
            invoice.warranty_count = len(warranty)

    def add_warranty(self):
        for rec in self:
            for lines in rec.invoice_line_ids:
                if lines.product_id.is_under_warranty:
                    if lines.product_id.tracking in ['serial','lot']:
                        for lot in lines.prod_lot_ids:
                            vals = {
                                'invoice_id':self.id,
                                'partner_id':self.partner_id.id,
                                'warranty_type':'free',
                                'warranty_term_id':lines.product_id.warranty_term_id.id,
                                'warranty_start_date':self.invoice_date,
                                'product_id':lines.product_id.id,
                                'lot_id':lot.id,
                            }
                            warranty = self.env['product.warranty'].create(vals)
                            warranty.onchnage_warranty_term()
                            warranty.confirm_warranty()
                    else:
                        vals = {
                            'invoice_id': self.id,
                            'partner_id': self.partner_id.id,
                            'warranty_type': 'free',
                            'warranty_term_id': lines.product_id.warranty_term_id.id,
                            'warranty_start_date': self.invoice_date,
                            'product_id': lines.product_id.id,
                            'product_qty': lines.quantity,
                        }
                        warranty = self.env['product.warranty'].create(vals)
                        warranty.onchnage_warranty_term()
                        warranty.confirm_warranty()
            rec.is_warranty_created = True


    def action_show_warranty(self):
        return {
            'name': _('Warranty'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'product.warranty',
            'domain': [('invoice_id', '=', self.id)],
            'context': "{'create': False}"
        }

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
            line.prod_lot_ids = line.mapped("stock_move_line_ids.move_line_ids.lot_id")

    def lots_grouped_by_quantity(self):
        lot_dict = defaultdict(float)
        for sml in self.mapped("stock_move_line_ids.move_line_ids"):
            lot_dict[sml.lot_id.name] += sml.qty_done
        return lot_dict

    def copy_data(self, default=None):
        self.ensure_one()
        res = super().copy_data(default=default)
        if (
            self.env.context.get("force_copy_stock_moves")
            and "stock_move_line_ids" not in res
        ):
            res[0]["stock_move_line_ids"] = [(6, 0, self.stock_move_line_ids.ids)]
        return res



