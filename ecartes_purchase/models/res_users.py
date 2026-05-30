from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    can_edit_confirmed_po = fields.Boolean(
        string="Can Edit Confirmed PO Description",
        compute='_compute_can_edit_confirmed_po',
        inverse='_inverse_can_edit_confirmed_po',
    )

    @api.depends('groups_id')
    def _compute_can_edit_confirmed_po(self):
        group = self.env.ref('ecartes_purchase.group_po_desc_edit')
        for user in self:
            user.can_edit_confirmed_po = group in user.groups_id

    def _inverse_can_edit_confirmed_po(self):
        group = self.env.ref('ecartes_purchase.group_po_desc_edit')
        for user in self:
            if user.can_edit_confirmed_po:
                user.sudo().write({'groups_id': [(4, group.id)]})
            else:
                user.sudo().write({'groups_id': [(3, group.id)]})
