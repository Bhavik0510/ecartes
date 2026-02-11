# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductWarranty(models.Model):
    _inherit = 'product.warranty'

    warranty_claim_ids = fields.One2many(comodel_name="helpdesk.ticket", inverse_name="product_warranty_id",
        string="Claims History")

    claim_count = fields.Integer(compute='compute_claim_count')

    def compute_claim_count(self):
        for record in self:
            record.claim_count = self.env['helpdesk.ticket'].search_count(
                [('product_warranty_id', '=', self.id)])

    
    def get_warranty(self):
        self.ensure_one()
        return {
            'name': _('Tickets'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'helpdesk.ticket',
            'domain': [('product_warranty_id', '=', self.id)],
            'context': "{'create': False}"
        }


    def create_warranty_claim(self):

        if self.product_id.type_of_claim == 'limited':
            claim_limit = self.product_id.no_of_claim

            if self.claim_count >= claim_limit:
                raise UserError('You have exceeded the maximum claim limit for this product.')

            else:
                self.write({'state': 'under_warranty'})
                data = {
                    'default_product_warranty_id': self.id,
                    'default_product_id': self.product_id.id,
                    'default_lot_ids': self.lot_ids.ids,
                    'default_product_qty': self.product_qty,
                    'default_partner_id': self.partner_id.id,
                }
        else:
            self.write({'state': 'under_warranty'})
            data = {
                'default_product_warranty_id': self.id,
                'default_product_id': self.product_id.id,
                'default_lot_ids': self.lot_ids.ids,
                'default_product_qty': self.product_qty,
                'default_partner_id': self.partner_id.id,
            }
        # data = {}
        return {
            'name': 'Create Ticket',
            'res_model': 'helpdesk.ticket',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            # 'view_id': self.env.ref("ecartes_product_warranty.warranty_claim_form_view").id,
            'target': 'new',
            "context": data,

        }

