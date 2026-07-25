from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    _order = 'create_date desc , date_order desc'

    responsible_person = fields.Char(string='Contact Person')
    deal_id = fields.Many2one('crm.lead', string='Deal', domain="[('type', '=','opportunity')]")
    shipping_mode = fields.Selection([('not_selected','Not Selected'),
                                ('by_air','By Air'),
                                ('by_hand','By Hand'),
                                ('by_cargo','By Cargo')],
                                "Shipping Mode")
    delivery_service = fields.Selection([('no_delivery', 'No Delivery'),
                                         ('courier', 'Courier'),
                                         ('local_pickup', 'Local Pickup')],
                                        "Delivery service")

    amc_id = fields.Many2one("amc.amc", string="AMC")
    amc_count = fields.Integer(compute='_compute_amc_count')

    @api.depends('amc_id')
    def _compute_amc_count(self):
        for order in self:
            order.amc_count = 1 if order.amc_id else 0

    def write(self, vals):
        res = super(SaleOrderInherit, self).write(vals)
        if not self.env.context.get('skip_amc_so_sync') and 'amc_id' in vals:
            for order in self:
                if order.amc_id and order.amc_id.sale_order_id != order:
                    order.amc_id.with_context(skip_amc_so_sync=True).write({
                        'sale_order_id': order.id,
                    })
        return res

    def action_show_amc(self):
        """Open linked AMC only (do not create from smart button)."""
        self.ensure_one()
        if not self.amc_id:
            raise ValidationError(_(
                "No AMC is linked to this Sales Order. "
                "Use the 'Create AMC' button after confirming the order."
            ))
        return {
            'name': _('AMC'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'amc.amc',
            'res_id': self.amc_id.id,
            'target': 'current',
        }

    def _prepare_amc_vals_from_sale(self):
        """Build AMC values from confirmed SO, including order lines."""
        self.ensure_one()
        product_lines = self.order_line.filtered(
            lambda line: not line.display_type and line.product_id
        )
        amc_product_lines = product_lines.filtered(
            lambda line: line.product_id.is_under_amc
        )
        lines_to_use = amc_product_lines or product_lines

        line_cmds = []
        for line in lines_to_use:
            line_cmds.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'price_unit': line.price_unit,
                'company_id': self.company_id.id,
                'tracking': line.product_id.tracking,
            }))

        amc_term = self.env['amc.term'].search([
            ('amc_by', '=', 'year'),
            ('total_no_of', '=', 1),
        ], limit=1)

        amount = sum(lines_to_use.mapped('price_subtotal')) or self.amount_untaxed
        return {
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'responsible_person': self.responsible_person or False,
            'amc_cost': 'paid',
            'amc_amt': amount,
            'total_amc_amount': amount,
            'amc_term_id': amc_term.id if amc_term else False,
            'line_ids': line_cmds,
        }

    def action_create_amc(self):
        """Create AMC from confirmed SO with customer, SO link and product lines."""
        self.ensure_one()
        if self.state not in ('sale', 'done'):
            raise ValidationError(_(
                "Please confirm the Sales Order before creating AMC."
            ))
        if self.amc_id:
            return self.action_show_amc()

        amc = self.env['amc.amc'].create(self._prepare_amc_vals_from_sale())
        if amc.amc_term_id:
            amc.onchnage_amc_term()
        amc._onchange_invoice_term()

        self.with_context(skip_amc_so_sync=True).write({'amc_id': amc.id})

        return {
            'name': _('AMC'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'amc.amc',
            'res_id': amc.id,
            'target': 'current',
        }

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not orderby and groupby:
            groupby_fields = groupby if isinstance(groupby, list) else [groupby]
            first_group_field = groupby_fields[0].split(':')[0]
            orderby = f'{first_group_field} desc'

        return super().read_group(
            domain, fields, groupby,
            offset=offset, limit=limit,
            orderby=orderby, lazy=lazy
        )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if res.get('opportunity_id'):
            res['deal_id'] = res.get('opportunity_id')
        return res


    @api.constrains('order_line')
    def check_product_price(self):
        group = self.env.user.has_group('ecartes_sale.minimum_cost_allowed_user')
        for rec in self:
            if not group:
                for record in rec.order_line:
                    if record.price_unit < record.product_id.minimum_cost:
                        raise ValidationError(
                            _("you can't enter Minimum price of this product {}".format(record.product_id.name)))
    
    def _prepare_invoice(self):
        res = super(SaleOrderInherit, self)._prepare_invoice()
        res.update({
             'deal': self.deal_id.id,
             'shipping_mode':self.shipping_mode,
             'responsible_person': self.responsible_person,
        })
        return res



class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    can_edit_price = fields.Boolean(compute='_compute_can_edit_price')
    can_edit_uom_qty = fields.Boolean(compute='_compute_can_edit_price')

    def _compute_can_edit_price(self):
        for line in self:
            line.can_edit_price = not line.env.user.has_group('ecartes_sale.group_access_user_change_price')
            line.can_edit_uom_qty = not line.env.user.has_group('ecartes_sale.group_access_user_change_quantity')

    price_unit = fields.Float('Unit Price',
                              # readonly=lambda line: not line.user.has_group(
                              #     'ecartes_sale.group_access_user_change_price'),
                              required=True, digits='Product Price', default=0.0)

    product_uom_qty = fields.Float(string='Quantity',
                                   # readonly=lambda line: not line.user.has_group(
                                   #     'ecartes_sale.group_access_user_change_quantity'),
                                   digits='Product Unit of Measure', required=True, default=1.0)


    
