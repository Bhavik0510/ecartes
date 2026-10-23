from odoo import models, fields, api, _

class ProductWarrantyLine(models.Model):
    _name = 'product.warranty.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Warranty Line'

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="[('is_under_warranty','=',True),'|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        check_company=True, required=True)

    lot_ids = fields.Many2many(
        'stock.lot', string='Lot/Serial',
        domain="[('product_id','=', product_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True)

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial (Single)',
        compute='_compute_lot_id', inverse='_inverse_lot_id', store=True,
        check_company=True)

    product_qty = fields.Float(
        'Product Quantity',
        default=1.0)

    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, required=True, index=True,
        default=lambda self: self.env.company)

    tracking = fields.Selection(
        related='product_id.tracking',
        store=True,
        readonly=True,
        string='Product Tracking')

    warranty_id = fields.Many2one('product.warranty', string='Warranty', ondelete='cascade')

    @api.depends('lot_ids')
    def _compute_lot_id(self):
        for rec in self:
            if rec.lot_ids:
                rec.lot_id = rec.lot_ids[0]
            elif rec.warranty_id and rec.warranty_id.lot_ids:
                matching = rec.warranty_id.lot_ids.filtered(lambda l: l.product_id == rec.product_id)
                if matching:
                    rec.lot_ids = [(6, 0, matching.ids)]
                    rec.lot_id = matching[0]
                else:
                    rec.lot_id = False
            else:
                rec.lot_id = False

    def _inverse_lot_id(self):
        for rec in self:
            if rec.lot_id and rec.lot_id not in rec.lot_ids:
                rec.lot_ids = [(4, rec.lot_id.id)]

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.tracking = self.product_id.tracking

    @api.onchange("lot_ids")
    def _onchange_lot_ids(self):
        if self.tracking == 'serial' and self.lot_ids:
            self.product_qty = float(len(self.lot_ids))

