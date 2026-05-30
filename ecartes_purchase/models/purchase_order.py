from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    order_line_readonly = fields.Boolean(compute='_compute_order_line_readonly')

    @api.depends('state')
    def _compute_order_line_readonly(self):
        has_group = self.env.user.has_group('ecartes_purchase.group_po_desc_edit')
        for order in self:
            order.order_line_readonly = (
                order.state == 'cancel'
                or (order.state == 'done' and not has_group)
            )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    can_edit_po_desc = fields.Boolean(compute='_compute_can_edit_po_desc')

    @api.depends('order_id.state')
    def _compute_can_edit_po_desc(self):
        has_group = self.env.user.has_group('ecartes_purchase.group_po_desc_edit')
        for line in self:
            line.can_edit_po_desc = (
                line.order_id.state not in ('purchase', 'done') or has_group
            )

    def write(self, vals):
        if 'name' in vals:
            for line in self:
                if line.order_id.state in ('purchase', 'done'):
                    if not self.env.user.has_group('ecartes_purchase.group_po_desc_edit'):
                        raise UserError(
                            "You don't have permission to edit the description of a confirmed Purchase Order."
                        )
        return super().write(vals)
