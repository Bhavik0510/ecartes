from odoo import api, fields, models,exceptions
from odoo.tools.float_utils import float_round, float_compare, float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cancel_done_picking = fields.Boolean(string='Cancel Done Delivery?', compute='check_cancel_done_picking')

    @api.model
    def check_cancel_done_picking(self):

        for picking in self:
            if picking.company_id.cancel_done_picking:
                picking.cancel_done_picking = True
            else:
                picking.cancel_done_picking = False

    def action_cancel(self):
        quant_obj = self.env['stock.quant']
        moves = self.env['account.move']
        return_picking_obj = self.env['stock.return.picking']
        account_move_obj = self.env['account.move']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for picking in self:
            if self.env.context.get('Flag', False) and picking.state == 'done':
                # Batch check for landed costs for all pickings at once
                landed_cost_rec = []
                try:
                    landed_cost_rec = self.env['stock.landed.cost'].search(
                        [('picking_ids', '=', picking.id), ('state', '=', 'done')])
                except:
                    pass

                if landed_cost_rec:
                    raise exceptions.Warning(
                        'This Delivery is set in landed cost record %s you need to delete it fisrt then you can cancel this Delivery' %
                        ','.join(landed_cost_rec.mapped('name')))

                # Filter moves once
                account_moves = picking.move_ids.filtered(lambda m: m.state != 'cancel')

                # Batch collect all move IDs for account move search
                move_ids = account_moves.ids

                # Single search for all account moves related to this picking
                all_acnt_moves = account_move_obj.search([('stock_move_id', 'in', move_ids)]) if move_ids else self.env[
                    'account.move']

                # Group account moves by stock_move_id for faster lookup
                acnt_moves_by_stock_move = {}
                for acnt_move in all_acnt_moves:
                    if acnt_move.stock_move_id.id not in acnt_moves_by_stock_move:
                        acnt_moves_by_stock_move[acnt_move.stock_move_id.id] = []
                    acnt_moves_by_stock_move[acnt_move.stock_move_id.id].append(acnt_move)

                # Collect all valuation layers to unlink in batch
                all_valuation_layers = self.env['stock.valuation.layer']

                for move in account_moves:
                    # Stock quantity updates
                    if move.state == "done" and move.product_id.type == "product":
                        # Batch prepare quant updates
                        for move_line in move.move_line_ids:
                            quantity = move_line.product_uom_id._compute_quantity(
                                move_line.quantity, move_line.product_id.uom_id)
                            quant_obj._update_available_quantity(
                                move_line.product_id, move_line.location_id,
                                quantity, move_line.lot_id)
                            quant_obj._update_available_quantity(
                                move_line.product_id, move_line.location_dest_id,
                                quantity * -1, move_line.lot_id)

                    # Update move state
                    if move.procure_method == 'make_to_order' and not move.move_orig_ids:
                        move.state = 'waiting'
                    elif move.move_orig_ids and not all(
                            orig.state in ('done', 'cancel') for orig in move.move_orig_ids):
                        move.state = 'waiting'
                    else:
                        move.state = 'confirmed'

                    siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
                    if move.propagate_cancel:
                        if all(state == 'cancel' for state in siblings_states):
                            move.move_dest_ids._action_cancel()
                    else:
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                        move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})

                    move.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})

                    # Collect valuation layers
                    if move.stock_valuation_layer_ids:
                        all_valuation_layers |= move.stock_valuation_layer_ids

                    # Process account moves from pre-fetched dictionary
                    acnt_moves = acnt_moves_by_stock_move.get(move.id, [])
                    if acnt_moves:
                        for acnt_move in acnt_moves:
                            acnt_move.with_context({'force_delete': True}).line_ids.sudo().remove_move_reconcile()
                            acnt_move.with_context({'force_delete': True}).button_cancel()
                            acnt_move.with_context({'force_delete': True}).unlink()

                # Batch unlink all valuation layers at once
                if all_valuation_layers:
                    all_valuation_layers.sudo().unlink()

        res = super(StockPicking, self).action_cancel()
        return res

    def action_draft(self):
        for res in self:
            if res.state =='cancel':
                res.state ='draft'
                res.move_ids.write({'state':'draft'})

        return True

    # @api.model
    # def create(self, vals):
    #     picking = super().create(vals)
    #
    #     if picking.picking_type_code == 'outgoing':
    #         move_lines = picking.move_ids_without_package
    #
    #         sorted_lines = move_lines.sorted(
    #             key=lambda line: line.product_id.categ_id.sequence or 0
    #         )
    #         for i, line in enumerate(sorted_lines):
    #             line.sequence = i
    #     return picking
    #
    # def write(self, vals):
    #     result = super().write(vals)
    #
    #     for picking in self:
    #         if picking.picking_type_code == 'outgoing':
    #             move_lines = picking.move_ids_without_package
    #
    #             sorted_lines = move_lines.sorted(
    #                 key=lambda line: line.product_id.categ_id.sequence or 0
    #             )
    #             for i, line in enumerate(sorted_lines):
    #                 line.sequence = i
    #
    #     return result
