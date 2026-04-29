# -*- coding: utf-8 -*-

import logging
import xmlrpc.client
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SyncManager(models.AbstractModel):
    _name = 'sync.manager'
    _description = 'Dynamic DB Connector'
    ATTACHMENT_SYNC_MODELS = [
        'account.move',    # invoices / bills
        'sale.order',      # sales
        'purchase.order',  # purchases
        'project.task',    # tasks
        'crm.lead',        # leads
    ]

    def _get_connection(self):
        params = self.env['ir.config_parameter'].sudo()
        url = params.get_param('odoo_db_connector.url')
        db = params.get_param('odoo_db_connector.db')
        username = params.get_param('odoo_db_connector.username')
        password = params.get_param('odoo_db_connector.password')

        if not all([url, db, username, password]):
            raise UserError(
                _("Receiver Database credentials are missing in Settings."))

        try:
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, username, password, {})
            if not uid:
                raise UserError(
                    _("Login failed for Receiver Database. Check Login/Password."))

            proxy = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
            return db, uid, password, proxy
        except Exception as e:
            raise UserError(_("Connection Error: %s") % str(e))

    def _get_target_company_id(self, db, uid, pwd, proxy):
        company_ids = proxy.execute_kw(db, uid, pwd, 'res.company', 'search',
                                       [[['is_invoice_target', '=', True]]], {'limit': 1})
        if not company_ids:
            raise UserError(
                _("No company in Receiver's Database has 'Is Invoice Target' checked."))
        return company_ids[0]

    def _receiver_has_connector_field(self, db, uid, pwd, proxy):
        """Check if receiver res.partner has connector_source_partner_id (odoo_db_receiver)."""
        try:
            fields = proxy.execute_kw(db, uid, pwd, 'res.partner', 'fields_get', [], {})
            return 'connector_source_partner_id' in fields
        except Exception:
            return False

    def sync_company_address(self, source_company, target_company_id, db, uid, pwd, proxy):
        """Ensure the target company has a valid address (country + state) before posting."""

        # Sync Country
        country_id_b = False
        if source_company.country_id:
            country_match = proxy.execute_kw(db, uid, pwd, 'res.country', 'search',
                                             [[['code', '=', source_company.country_id.code]]],
                                             {'limit': 1})
            if country_match:
                country_id_b = country_match[0]

        # Sync State
        state_id_b = False
        if source_company.state_id:
            state_domain = [['code', '=', source_company.state_id.code]]
            if country_id_b:
                state_domain.append(['country_id', '=', country_id_b])
            state_match = proxy.execute_kw(db, uid, pwd, 'res.country.state', 'search',
                                           [state_domain], {'limit': 1})
            if state_match:
                state_id_b = state_match[0]

        # Get the partner_id linked to the target company
        company_data = proxy.execute_kw(db, uid, pwd, 'res.company', 'read',
                                        [target_company_id], {'fields': ['partner_id']})
        partner_id = company_data[0]['partner_id'][0]

        update_vals = {
            'street': source_company.street or '',
            'street2': source_company.street2 or '',
            'city': source_company.city or '',
            'zip': source_company.zip or '',
            'country_id': country_id_b,
            'state_id': state_id_b,
        }

        proxy.execute_kw(db, uid, pwd, 'res.partner', 'write', [[partner_id], update_vals])

    def sync_uom(self, uom, db, uid, pwd, proxy):
        """Sync unit of measure to target DB, create if not exists."""
        if not uom:
            return False

        # If UoM already exists on target, return it
        uom_match = proxy.execute_kw(db, uid, pwd, 'uom.uom', 'search',
                                     [[['name', '=', uom.name]]], {'limit': 1})
        if uom_match:
            return uom_match[0]

        # Find or create the UoM category first
        category_match = proxy.execute_kw(db, uid, pwd, 'uom.category', 'search',
                                          [[['name', '=', uom.category_id.name]]], {'limit': 1})
        if category_match:
            category_id_b = category_match[0]
        else:
            category_id_b = proxy.execute_kw(db, uid, pwd, 'uom.category', 'create',
                                             [{'name': uom.category_id.name}])

        # If source UoM is a reference unit, check if target category already has one.
        # If so, create as 'bigger' with factor 1 to avoid the unique reference constraint.
        uom_type = uom.uom_type
        if uom_type == 'reference':
            existing_ref = proxy.execute_kw(db, uid, pwd, 'uom.uom', 'search',
                                            [[['category_id', '=', category_id_b],
                                              ['uom_type', '=', 'reference']]],
                                            {'limit': 1})
            if existing_ref:
                uom_type = 'bigger'

        new_uom_id = proxy.execute_kw(db, uid, pwd, 'uom.uom', 'create', [{
            'name': uom.name,
            'category_id': category_id_b,
            'factor': uom.factor,
            'factor_inv': uom.factor_inv,
            'rounding': uom.rounding,
            'uom_type': uom_type,
        }])
        return new_uom_id

    def _find_matching_attachment_on_receiver(self, db, uid, pwd, proxy, target_res_model, target_res_id, attachment):
        """Find existing receiver attachment for same business record."""
        domain = [
            ['res_model', '=', target_res_model],
            ['res_id', '=', target_res_id],
            ['type', '=', 'binary'],
            ['name', '=', attachment.name or 'Attachment'],
            ['mimetype', '=', attachment.mimetype or False],
            ['file_size', '=', attachment.file_size or 0],
        ]
        existing_ids = proxy.execute_kw(
            db, uid, pwd, 'ir.attachment', 'search',
            [domain], {'limit': 1}
        )
        return existing_ids[0] if existing_ids else False

    def _payload_to_base64_text(self, payload):
        """Normalize payload to plain base64 text for XML-RPC write/create."""
        if isinstance(payload, xmlrpc.client.Binary):
            payload = payload.data
        if isinstance(payload, memoryview):
            payload = payload.tobytes()
        if isinstance(payload, bytes):
            payload = payload.decode('ascii')
        if isinstance(payload, str):
            return payload
        return False

    def _sync_move_attachments(self, source_move, target_move_id, db, uid, pwd, proxy):
        """Push invoice/bill binary attachments to receiver DB."""
        source_attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', source_move.id),
            ('type', '=', 'binary'),
        ])
        for attachment in source_attachments:
            if self._find_matching_attachment_on_receiver(
                db, uid, pwd, proxy, 'account.move', target_move_id, attachment
            ):
                continue

            payload = self._payload_to_base64_text(attachment.datas)
            if not payload:
                continue

            vals = {
                'name': attachment.name or 'Attachment',
                'type': 'binary',
                'datas': payload,
                'res_model': 'account.move',
                'res_id': target_move_id,
                'mimetype': attachment.mimetype or False,
            }
            proxy.execute_kw(db, uid, pwd, 'ir.attachment', 'create', [vals])

    def _receiver_record_exists(self, db, uid, pwd, proxy, model_name, res_id):
        """Check that related business record exists on receiver DB."""
        ids = proxy.execute_kw(
            db, uid, pwd, model_name, 'search',
            [[['id', '=', int(res_id)]]], {'limit': 1}
        )
        return bool(ids)

    def _sync_single_attachment_to_receiver(self, attachment, db, uid, pwd, proxy):
        """Push one attachment if receiver has same res_model/res_id record."""
        if not attachment.res_model or not attachment.res_id:
            return False
        if not self._receiver_record_exists(
            db, uid, pwd, proxy, attachment.res_model, attachment.res_id
        ):
            return False

        payload = self._payload_to_base64_text(attachment.datas)
        if not payload:
            return False

        write_vals = {
            'name': attachment.name or 'Attachment',
            'type': 'binary',
            'datas': payload,
            'res_model': attachment.res_model,
            'res_id': attachment.res_id,
            'mimetype': attachment.mimetype or False,
        }

        # 1) If same ID exists on receiver, update it (best for migrated DBs).
        same_id = proxy.execute_kw(
            db, uid, pwd, 'ir.attachment', 'search',
            [[['id', '=', attachment.id]]], {'limit': 1}
        )
        if same_id:
            proxy.execute_kw(db, uid, pwd, 'ir.attachment', 'write', [same_id, write_vals])
            return True

        # 2) If matching metadata exists, update it (fixes empty migrated attachment rows).
        matched_id = self._find_matching_attachment_on_receiver(
            db, uid, pwd, proxy, attachment.res_model, attachment.res_id, attachment
        )
        if matched_id:
            proxy.execute_kw(db, uid, pwd, 'ir.attachment', 'write', [[matched_id], write_vals])
            return True

        # 3) Otherwise create new.
        proxy.execute_kw(db, uid, pwd, 'ir.attachment', 'create', [write_vals])
        return True

    def sync_all_attachments_to_receiver(self, batch_size=100):
        """
        Scheduled action:
        Incrementally sync attachments to receiver for selected business models.
        Uses last-synced attachment ID checkpoint to keep each run lightweight.
        """
        batch_size = int(batch_size or 100)
        if batch_size < 1:
            batch_size = 100

        params = self.env['ir.config_parameter'].sudo()
        checkpoint_key = 'odoo_db_connector.attachment_last_synced_id'
        last_synced_id = int(params.get_param(checkpoint_key, '0') or 0)

        db, uid, pwd, proxy = self._get_connection()
        attachment_model = self.env['ir.attachment'].sudo()
        domain = [
            ('id', '>', last_synced_id),
            ('type', '=', 'binary'),
            ('res_model', 'in', self.ATTACHMENT_SYNC_MODELS),
        ]
        attachments = attachment_model.search(domain, order='id asc', limit=batch_size)
        if not attachments:
            _logger.info("[attachment_sync] No new attachments after id=%s", last_synced_id)
            return

        synced = skipped = 0
        max_seen_id = last_synced_id
        for attachment in attachments:
            max_seen_id = max(max_seen_id, attachment.id)
            try:
                did_sync = self._sync_single_attachment_to_receiver(
                    attachment, db, uid, pwd, proxy
                )
                if did_sync:
                    synced += 1
                else:
                    skipped += 1
            except Exception as e:
                skipped += 1
                _logger.warning(
                    "[attachment_sync] Failed attachment id=%s model=%s res_id=%s: %s",
                    attachment.id, attachment.res_model, attachment.res_id, e
                )

        params.set_param(checkpoint_key, str(max_seen_id))
        _logger.info(
            "[attachment_sync] Done upto id=%s, synced=%s skipped=%s fetched=%s",
            max_seen_id, synced, skipped, len(attachments)
        )

    def push_invoice(self, invoice):
        db, uid, pwd, proxy = self._get_connection()
        target_company_id = self._get_target_company_id(db, uid, pwd, proxy)

        # Sync source company address to target company before posting
        self.sync_company_address(invoice.company_id, target_company_id, db, uid, pwd, proxy)

        partner_id_b = self.sync_partner(
            invoice.partner_id, target_company_id, db, uid, pwd, proxy)
        ctx = {'default_company_id': target_company_id,
               'allowed_company_ids': [target_company_id]}
        invoice_vals = {
            'name' : invoice.name,
            'move_type': invoice.move_type,
            'partner_id': partner_id_b,
            'invoice_date': str(invoice.invoice_date),
            'invoice_date_due': str(invoice.invoice_date_due),
            'ref': invoice.name,
            'company_id': target_company_id,
            'invoice_line_ids': []
        }
        for line in invoice.invoice_line_ids:
            if line.display_type == 'product' and line.product_id:
                product_id_b = self.push_product(
                    line.product_id, db, uid, pwd, proxy)
                tax_ids_b = []
                for tax in line.tax_ids:
                    # Find matching tax by name on target DB
                    tax_match = proxy.execute_kw(db, uid, pwd, 'account.tax', 'search',
                                                 [[['name', '=', tax.name],
                                                   ['company_id', '=', target_company_id]]],
                                                 {'limit': 1})
                    if tax_match:
                        tax_ids_b.append(tax_match[0])

                line_vals = {
                    'name': line.name,
                    'product_id': product_id_b,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'tax_ids': [(6, 0, tax_ids_b)],
                    'company_id': target_company_id,
                }
                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
        try:
            new_invoice_ids = proxy.execute_kw(
                db, uid, pwd, 'account.move', 'create',
                [[invoice_vals]],          # ← double-wrapped: [vals_list]
                {'context': ctx}
            )
            new_invoice_id = new_invoice_ids[0]   # extract the single ID from the returned list
            proxy.execute_kw(
                db, uid, pwd, 'account.move', 'action_post',
                [[new_invoice_id]],        # action_post also expects a list of IDs
                {'context': ctx}
            )
            self._sync_move_attachments(invoice, new_invoice_id, db, uid, pwd, proxy)
            return new_invoice_id
        except Exception as e:
            raise UserError(_("Receiver Database has rejected the invoice: %s") % str(e))

    def delete_invoice_on_receiver(self, remote_move_id):
        """Set the move to draft on receiver DB (if posted), then unlink. Each step in its own try so unlink always runs."""
        if not remote_move_id:
            return
        db, uid, pwd, proxy = self._get_connection()
        target_company_id = self._get_target_company_id(db, uid, pwd, proxy)
        ctx = {'default_company_id': target_company_id, 'allowed_company_ids': [target_company_id]}
        remote_move_id = int(remote_move_id)
        ids_to_unlink = [remote_move_id]

        # Step 1: read state (optional; if response is None-fault we continue anyway)
        move_data = None
        try:
            move_data = proxy.execute_kw(
                db, uid, pwd, 'account.move', 'read',
                [[remote_move_id]], {'fields': ['state'], 'context': ctx}
            )
        except xmlrpc.client.Fault as e:
            if "cannot marshal None" in str(e):
                _logger.info("[delete_invoice_on_receiver] read: move id=%s got None in response (continuing).", remote_move_id)
            else:
                _logger.warning("[delete_invoice_on_receiver] read failed for id=%s: %s", remote_move_id, e)
        except Exception as e:
            _logger.warning("[delete_invoice_on_receiver] read failed for id=%s: %s", remote_move_id, e)

        # Step 2: set to draft if not already (so unlink is allowed)
        need_draft = not (move_data and len(move_data) and move_data[0].get('state') == 'draft')
        if need_draft:
            try:
                proxy.execute_kw(
                    db, uid, pwd, 'account.move', 'button_draft',
                    [[remote_move_id]], {'context': ctx}
                )
                _logger.info("[delete_invoice_on_receiver] Set move id=%s to draft on receiver.", remote_move_id)
            except xmlrpc.client.Fault as e:
                if "cannot marshal None" in str(e):
                    _logger.info("[delete_invoice_on_receiver] button_draft id=%s got None in response (continuing to unlink).", remote_move_id)
                else:
                    _logger.warning("[delete_invoice_on_receiver] button_draft failed for id=%s: %s", remote_move_id, e)
            except Exception as e:
                _logger.warning("[delete_invoice_on_receiver] button_draft failed for id=%s: %s", remote_move_id, e)

        # Step 3: always call unlink (this is what actually deletes)
        _logger.info("[delete_invoice_on_receiver] Calling unlink for move id=%s on receiver DB.", remote_move_id)
        try:
            proxy.execute_kw(
                db, uid, pwd, 'account.move', 'unlink',
                [ids_to_unlink], {'context': ctx}
            )
            _logger.info("[delete_invoice_on_receiver] Deleted move id=%s on receiver DB.", remote_move_id)
        except xmlrpc.client.Fault as e:
            if "cannot marshal None" in str(e):
                _logger.info(
                    "[delete_invoice_on_receiver] Unlink id=%s returned None in response (delete likely succeeded on receiver).",
                    remote_move_id
                )
            else:
                _logger.warning("[delete_invoice_on_receiver] Unlink failed for id=%s: %s", remote_move_id, e)
        except Exception as e:
            _logger.warning("[delete_invoice_on_receiver] Unlink failed for id=%s: %s", remote_move_id, e)

    def delete_invoice_on_receiver_by_name(self, name, move_type):
        """Find move on receiver by name + move_type, set draft if needed, then unlink. Each step in its own try so unlink always runs."""
        if not name or move_type not in ('out_invoice', 'in_invoice', 'out_refund', 'in_refund'):
            return
        db, uid, pwd, proxy = self._get_connection()
        target_company_id = self._get_target_company_id(db, uid, pwd, proxy)
        ctx = {'default_company_id': target_company_id, 'allowed_company_ids': [target_company_id]}

        # Step 1: search by name
        ids = []
        try:
            ids = proxy.execute_kw(
                db, uid, pwd, 'account.move', 'search',
                [[['name', '=', name], ['move_type', '=', move_type], ['company_id', '=', target_company_id]]],
                {'limit': 1, 'context': ctx}
            )
        except xmlrpc.client.Fault as e:
            if "cannot marshal None" in str(e):
                _logger.info("[delete_invoice_on_receiver_by_name] search name=%s got None (continuing).", name)
            else:
                _logger.warning("[delete_invoice_on_receiver_by_name] search failed name=%s: %s", name, e)
            return
        except Exception as e:
            _logger.warning("[delete_invoice_on_receiver_by_name] search failed name=%s: %s", name, e)
            return
        if not ids:
            _logger.info("[delete_invoice_on_receiver_by_name] No move name=%s on receiver.", name)
            return
        remote_id = ids[0]

        # Step 2: read state then set to draft if needed
        move_data = None
        try:
            move_data = proxy.execute_kw(
                db, uid, pwd, 'account.move', 'read',
                [[remote_id]], {'fields': ['state'], 'context': ctx}
            )
        except (xmlrpc.client.Fault, Exception) as e:
            if "cannot marshal None" in str(e):
                _logger.info("[delete_invoice_on_receiver_by_name] read name=%s got None (continuing).", name)
            else:
                _logger.warning("[delete_invoice_on_receiver_by_name] read failed name=%s: %s", name, e)
        need_draft = not (move_data and len(move_data) and move_data[0].get('state') == 'draft')
        if need_draft:
            try:
                proxy.execute_kw(db, uid, pwd, 'account.move', 'button_draft', [[remote_id]], {'context': ctx})
                _logger.info("[delete_invoice_on_receiver_by_name] Set name=%s id=%s to draft.", name, remote_id)
            except xmlrpc.client.Fault as e:
                if "cannot marshal None" in str(e):
                    _logger.info("[delete_invoice_on_receiver_by_name] button_draft name=%s got None (continuing to unlink).", name)
                else:
                    _logger.warning("[delete_invoice_on_receiver_by_name] button_draft name=%s: %s", name, e)
            except Exception as e:
                _logger.warning("[delete_invoice_on_receiver_by_name] button_draft name=%s: %s", name, e)

        # Step 3: always call unlink
        _logger.info("[delete_invoice_on_receiver_by_name] Calling unlink for name=%s id=%s on receiver.", name, remote_id)
        try:
            proxy.execute_kw(db, uid, pwd, 'account.move', 'unlink', [[remote_id]], {'context': ctx})
            _logger.info("[delete_invoice_on_receiver_by_name] Deleted move name=%s id=%s on receiver.", name, remote_id)
        except xmlrpc.client.Fault as e:
            if "cannot marshal None" in str(e):
                _logger.info("[delete_invoice_on_receiver_by_name] Unlink name=%s returned None (delete likely succeeded).", name)
            else:
                _logger.warning("[delete_invoice_on_receiver_by_name] Unlink failed name=%s: %s", name, e)
        except Exception as e:
            _logger.warning("[delete_invoice_on_receiver_by_name] Unlink failed name=%s: %s", name, e)

    def push_customer_from_quotation(self, order):
        db, uid, pwd, proxy = self._get_connection()
        target_company_id = self._get_target_company_id(db, uid, pwd, proxy)

        # Sync source company address to target company before posting
        self.sync_company_address(order.company_id, target_company_id, db, uid, pwd, proxy)

        # Sync the partner
        return self.sync_partner(order.partner_id, target_company_id, db, uid, pwd, proxy)

    def sync_partner(self, partner, company_id, db, uid, pwd, proxy, log_detail=False, receiver_has_connector_field=None):
        # 1) Search by source partner ID first (receiver has connector_source_partner_id) -> one source partner = one receiver partner, no duplicates
        # 2) If not found, search by name in target company -> update and link source id
        # 3) If not found, create and set source id
        if receiver_has_connector_field is None:
            receiver_has_connector_field = self._receiver_has_connector_field(db, uid, pwd, proxy)
        ctx = {'default_company_id': company_id, 'allowed_company_ids': [company_id]}
        company_domain = ['|', ['company_id', '=', False], ['company_id', '=', company_id]]

        # Search by connector_source_partner_id only if receiver has the field
        partner_ids = []
        if receiver_has_connector_field:
            source_id_domain = ['&', ['connector_source_partner_id', '=', partner.id]] + company_domain
            try:
                partner_ids = proxy.execute_kw(
                    db, uid, pwd, 'res.partner', 'search', [source_id_domain], {'limit': 1, 'context': ctx})
            except Exception as e:
                if log_detail:
                    _logger.info("[sync_partner] search by source id failed: %s", e)

        if not partner_ids:
            # Fallback: search by name in target company
            name_domain = [['name', '=', partner.name]]
            domain = ['&'] + company_domain + name_domain
            if log_detail:
                _logger.info(
                    "[sync_partner] source id=%s name=%r search_domain=%s",
                    partner.id, partner.name, domain
                )
            try:
                partner_ids = proxy.execute_kw(
                    db, uid, pwd, 'res.partner', 'search', [domain], {'limit': 1, 'context': ctx})
            except Exception as e:
                _logger.exception(
                    "[sync_partner] receiver search FAILED for id=%s %r: %s",
                    partner.id, partner.name, e
                )
                raise
        if log_detail:
            _logger.info(
                "[sync_partner] source id=%s receiver search result: partner_ids=%s",
                partner.id, partner_ids
            )

        # Sync Country by code
        country_id_b = False
        if partner.country_id:
            country_match = proxy.execute_kw(db, uid, pwd, 'res.country', 'search',
                                             [[['code', '=', partner.country_id.code]]],
                                             {'limit': 1})
            if country_match:
                country_id_b = country_match[0]

        # Sync State by code (and country to avoid duplicates)
        state_id_b = False
        if partner.state_id:
            state_domain = [['code', '=', partner.state_id.code]]
            if country_id_b:
                state_domain.append(['country_id', '=', country_id_b])
            state_match = proxy.execute_kw(db, uid, pwd, 'res.country.state', 'search',
                                           [state_domain], {'limit': 1})
            if state_match:
                state_id_b = state_match[0]

        # So partner shows as Customer/Supplier on receiver (contacts filter by these)
        customer_rank = getattr(partner, 'customer_rank', 0)
        supplier_rank = getattr(partner, 'supplier_rank', 0)

        partner_vals = {
            'name': partner.name,
            'email': partner.email or '',
            'l10n_in_gst_treatment': partner.l10n_in_gst_treatment or '',
            'l10n_in_pan': partner.l10n_in_pan or '',
            'street': partner.street or '',
            'street2': partner.street2 or '',
            'city': partner.city or '',
            'zip': partner.zip or '',
            'phone': partner.phone or '',
            'mobile': partner.mobile or '',
            'vat': partner.vat or '',
            'company_id': company_id,
            'is_company': partner.is_company,
            'country_id': country_id_b,
            'state_id': state_id_b,
            'customer_rank': customer_rank,
            'supplier_rank': supplier_rank,
        }
        # Only send if receiver has the field (odoo_db_receiver installed & upgraded)
        if receiver_has_connector_field:
            partner_vals['connector_source_partner_id'] = partner.id
        if log_detail:
            _logger.info(
                "[sync_partner] source id=%s partner_vals (keys): %s customer_rank=%s supplier_rank=%s",
                partner.id, list(partner_vals.keys()), customer_rank, supplier_rank
            )

        if not partner_ids:
            if log_detail:
                _logger.info("[sync_partner] source id=%s -> CREATE on receiver", partner.id)
            try:
                new_id = proxy.execute_kw(
                    db, uid, pwd, 'res.partner', 'create', [partner_vals], {'context': ctx})
                if log_detail:
                    _logger.info("[sync_partner] source id=%s -> CREATE ok receiver partner_id=%s", partner.id, new_id)
                return new_id
            except Exception as e:
                _logger.exception(
                    "[sync_partner] source id=%s CREATE FAILED on receiver: %s",
                    partner.id, e
                )
                raise
        else:
            if log_detail:
                _logger.info("[sync_partner] source id=%s -> WRITE receiver partner_ids=%s", partner.id, partner_ids)
            try:
                proxy.execute_kw(
                    db, uid, pwd, 'res.partner', 'write',
                    [partner_ids, partner_vals], {'context': ctx})
                if log_detail:
                    _logger.info("[sync_partner] source id=%s -> WRITE ok", partner.id)
                return partner_ids[0]
            except Exception as e:
                _logger.exception(
                    "[sync_partner] source id=%s WRITE FAILED on receiver: %s",
                    partner.id, e
                )
                raise

    def push_product(self, product, db, uid, pwd, proxy):
        if not product.name:
            raise UserError(
                _("Product '%s' must have an name to be synced.") % product.name)
        existing = proxy.execute_kw(db, uid, pwd, 'product.product', 'search',
                                    [[['name', '=', product.name]]])

        if not existing:
            # Sync product UoM and Purchase UoM only when creating the product
            uom_id_b = self.sync_uom(product.uom_id, db, uid, pwd, proxy)
            uom_po_id_b = self.sync_uom(product.uom_po_id, db, uid, pwd, proxy)

            product_vals = {
                'name': product.name,
                'default_code': product.default_code,
                'lst_price': product.lst_price or 0,
                'standard_price': product.standard_price or 0,
                'type': 'consu',
                'is_storable': True,
            }
            if uom_id_b:
                product_vals['uom_id'] = uom_id_b
            if uom_po_id_b:
                product_vals['uom_po_id'] = uom_po_id_b

            return proxy.execute_kw(db, uid, pwd, 'product.product', 'create', [product_vals])
        else:
            # Product already exists and may be used in posted entries on receiver.
            # Do NOT try to change its UoM there, only update safe fields.
            product_vals = {
                'name': product.name,
                'default_code': product.default_code,
                'lst_price': product.lst_price or 0,
                'standard_price': product.standard_price or 0,
                'type': 'consu',
                'is_storable': True,
            }
            proxy.execute_kw(
                db, uid, pwd, 'product.product', 'write', [existing, product_vals]
            )
            return existing[0]
