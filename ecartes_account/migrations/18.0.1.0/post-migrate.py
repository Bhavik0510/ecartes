# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0.html)


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    from odoo.addons.ecartes_account.hooks import strip_kanban_from_invoice_window_actions

    strip_kanban_from_invoice_window_actions(env)
