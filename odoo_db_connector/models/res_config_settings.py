# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    db_receiver_url = fields.Char(
        string="Receiver Database URL", config_parameter='odoo_db_connector.url')
    db_receiver_name = fields.Char(
        string="Receiver Database Name", config_parameter='odoo_db_connector.db')
    db_receiver_username = fields.Char(
        string="Receiver Database Login Email", config_parameter='odoo_db_connector.username')
    db_receiver_password = fields.Char(
        string="Receiver Database Password", config_parameter='odoo_db_connector.password')

    def action_connect_and_setup_receiver_db(self):
        sync_manager = self.env['sync.manager']
        db, uid, pwd, proxy = sync_manager._get_connection()
        message = "Connection Successful! "
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _(message + "Target company found and ready."),
                'sticky': False,
                'type': 'success',
            }
        }
