from odoo import fields, models, api, _, tools
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    def _valid_field_parameter(self, field, name):
        # allow specifying rendering options directly from field when using the render mixin
        return name in ['tracking'] or super()._valid_field_parameter(field, name)

    gst_no = fields.Char("GSTIN", tracking=True)
    user_name = fields.Char("User Name", tracking=True)
    user_password = fields.Char("Password", tracking=True)
    auth_token = fields.Char('Auth-Token', tracking=True)
    expire_date = fields.Datetime('Token Expiry Date', tracking=True)
    expire_date1 = fields.Char('Token Expiry Date1', tracking=True)

   
    