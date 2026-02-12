#  vim:ts=8:sts=4:sw=4:tw=0:et:si:fileencoding=utf-8 :
# -*- coding: utf-8 -*-
# This file is part of TeXByte GST module. See LICENSE for details

from odoo import models, api


''' Account Invoice '''
class GSTInvoice(models.Model):
    _inherit = 'account.move'


    ''' Methods '''
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        #Remove tax lines, after fiscal position is set, recompute the tax lines
        result = super(GSTInvoice, self)._onchange_partner_id()
        self._onchange_fiscal_position_id()
        return result

    """ Ensure to reapply taxes on lines when fiscal position changes """
    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_id(self):
        for line in self.invoice_line_ids:
            line.tax_ids = line._get_computed_taxes()

    def _is_reverse_charge_applicable(self):
        if self.move_type in ('in_invoice', 'in_refund') and self.partner_id and not self.partner_id.vat and not self.l10n_in_gst_treatment == 'overseas':
            return True
        else:
            return False
