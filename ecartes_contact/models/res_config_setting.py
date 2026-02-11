# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_duplicate_contacts = fields.Boolean("Restrict Duplicate Contacts")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['restrict_duplicate_contacts'] = self.env['ir.config_parameter'].sudo().get_param('ecartes_contact.restrict_duplicate_contacts')
        return res
        
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ecartes_contact.restrict_duplicate_contacts', self.restrict_duplicate_contacts)
        return res