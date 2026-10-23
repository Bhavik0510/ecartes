from odoo import api, fields, models,_

class AMC(models.Model):
    _inherit = 'amc.amc'

    product_warrenty_id = fields.Many2one(comodel_name="product.warranty", string="Product Warrenty")
    product_warrenty_ids = fields.Many2many("product.warranty","amc_warrenry_rel",string="Product Warrenties")
    warranty_ref = fields.Char(
        string='Warranty Ref No',
        compute='_compute_warranty_ref',
        inverse='_inverse_warranty_ref',
        store=True,
        readonly=False,
        tracking=True,
    )

    @api.depends('product_warrenty_ids.name', 'product_warrenty_id.name')
    def _compute_warranty_ref(self):
        for rec in self:
            names = []
            if rec.product_warrenty_ids:
                names = [w.name for w in rec.product_warrenty_ids if w.name]
            elif rec.product_warrenty_id and rec.product_warrenty_id.name:
                names = [rec.product_warrenty_id.name]
            if names:
                rec.warranty_ref = ', '.join(names)
            elif not rec.warranty_ref:
                rec.warranty_ref = False

    def _inverse_warranty_ref(self):
        for rec in self:
            if rec.warranty_ref and not rec.product_warrenty_ids:
                warranties = self.env['product.warranty'].search([('name', '=', rec.warranty_ref.strip())], limit=1)
                if warranties:
                    rec.product_warrenty_ids = [(4, warranties.id)]
                    rec.product_warrenty_id = warranties.id

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
