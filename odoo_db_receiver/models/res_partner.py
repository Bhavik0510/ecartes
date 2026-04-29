# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    connector_source_partner_id = fields.Integer(
        string='Connector Source Partner ID',
        copy=False,
        index=True,
        help='Partner ID from the source database (Odoo DB Connector). '
             'Used to avoid creating duplicates when re-syncing.',
    )

    @api.model
    def _auto_init(self):
        """Ensure column exists (handles upgrade where ORM did not create it)."""
        res = super()._auto_init()
        self.env.cr.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'res_partner' AND column_name = 'connector_source_partner_id'
        """)
        if not self.env.cr.fetchone():
            self.env.cr.execute("""
                ALTER TABLE res_partner
                ADD COLUMN IF NOT EXISTS connector_source_partner_id integer
            """)
            self.env.cr.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS connector_source_partner_id_uniq
                ON res_partner (connector_source_partner_id)
                WHERE connector_source_partner_id IS NOT NULL
            """)
            self.env.registry.clear_cache()
        return res
