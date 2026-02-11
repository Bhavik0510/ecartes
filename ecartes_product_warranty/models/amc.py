from odoo import api, fields, models,_

class AMC(models.Model):
    _inherit = 'amc.amc'

    product_warrenty_id = fields.Many2one(comodel_name="product.warranty", string="Product Warrenty")
    product_warrenty_ids = fields.Many2many("product.warranty","amc_warrenry_rel",string="Product Warrenties")


    warranty_count = fields.Integer(
        string="Warranty", compute="_compute_warranty_ids"
    )


    def _compute_warranty_ids(self):
        self.warranty_count=False
        for rec in self:
            warranty = self.env['product.warranty'].search([('id','in',self.product_warrenty_ids.ids)]).ids
            rec.warranty_count = len(warranty)    

  
    def action_show_warranty(self):
          return {
            'name': _('Warranty'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'product.warranty',
            'domain': [('id', 'in', self.product_warrenty_ids.ids)],
            'context': "{'create': False}"
        }
