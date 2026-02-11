# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.user.has_group('vx_sale.group_access_readonly_contact'):
            raise ValidationError(_("You can't Create Contact/Customer/Supplier, Please Contact Your Administrator or Manager."))
        return super(Partner, self).create(vals_list)
