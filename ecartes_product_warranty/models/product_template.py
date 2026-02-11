from odoo import api, fields, models

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    is_under_warranty = fields.Boolean(string="Under Warranty")
    allow_renewal = fields.Boolean(string="Allow Renewal")
    allow_sale_order = fields.Boolean(string="Allow Warranty Create From Sale Order")

    type_of_claim = fields.Selection(string="Claim Type", selection=[('limited', 'Limited'), ('unlimited', 'Unlimited')],
                                  default="unlimited", tracking=True, )
    no_of_claim = fields.Integer(string="No. Of Claim")

    warranty_term_id = fields.Many2one(comodel_name="warranty.term", string="Default Warranty Term")