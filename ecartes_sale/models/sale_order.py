from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

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



    
