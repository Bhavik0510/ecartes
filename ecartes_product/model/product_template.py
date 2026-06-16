from odoo import fields, models, api, _
from odoo.exceptions import AccessError

class Products(models.Model):
    _inherit = 'product.template'

    p_id = fields.Integer(string='P-ID')
    sort = fields.Integer(string='Sort')
    section = fields.Char(string='Section ')
    minimum_cost = fields.Float(string='Minimum Cost Allowed')

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('product.group_product_manager'):
            raise AccessError(_("You do not have permission to create products. Please enable 'Product Creation' in your user settings."))
        product_ids = super(Products,self).create(vals_list)
        for product_id in product_ids:
            product_id.write({'p_id':product_id.id})
        return product_ids


class ProductInh(models.Model):
    _inherit = 'product.product'

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('product.group_product_manager'):
            raise AccessError(_("You do not have permission to create products. Please enable 'Product Creation' in your user settings."))
        return super(ProductInh, self).create(vals_list)

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        # name = self.display_name
        if self.description_sale:
            name = self.description_sale
        else:
            name = ''
        return name