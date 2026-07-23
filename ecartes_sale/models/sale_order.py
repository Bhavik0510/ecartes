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
        self.ensure_one()
        if not self.amc_id:
            return self.action_create_amc()
        return {
            'name': _('AMC'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'amc.amc',
            'res_id': self.amc_id.id,
            'target': 'current',
        }

    def action_create_amc(self):
        self.ensure_one()
        return {
            'name': _('AMC'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'amc.amc',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_sale_order_id': self.id,
                'default_user_id': self.user_id.id,
            },
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


    
