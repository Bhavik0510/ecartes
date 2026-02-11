# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    partner_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    description = fields.Html(required=True, sanitize_style=True, tracking=True)
    partner_name = fields.Char(string="Contact Person")
    partner_phone = fields.Char(string="Phone")
    partner_mobile = fields.Char(string="Mobile")

    product_id = fields.Many2one(
        'product.product', string='Product',
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        required=True, check_company=True, tracking=True)
    lot_ids = fields.Many2many(
        'stock.lot', string='Lot/Serial', tracking=True,
        domain="[('product_id','=', product_id), ('company_id', '=', company_id)]", check_company=True)
    product_qty = fields.Float('Product Quantity', default=1.0, tracking=True, required=True)
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string='Product Tracking', readonly=False)

    customer_invoice_id = fields.Many2one("account.move", string="Customer Invoice", copy=False)
    amc_id = fields.Many2one("amc.amc", string="AMC", copy=False)
    product_warranty_id = fields.Many2one("product.warranty", string="Product Warranty", copy=False)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = ''
            self.partner_email = self.partner_id.email
            self.partner_phone = self.partner_id.phone
            self.partner_mobile = self.partner_id.mobile

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.tracking = self.product_id.tracking
