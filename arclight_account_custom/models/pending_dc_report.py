# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time

from odoo import api, fields, models
from odoo.tools import float_compare


class PendingDcReport(models.TransientModel):
    """Wizard for Pending DC (Delivery Challan) Report - Sales Bills Pending."""

    _name = 'pending.dc.report'
    _description = 'Pending DC Report'

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        default=lambda self: fields.Date.today(),
    )

    def action_export_excel(self):
        """Download Excel report for the selected date range."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/arclight_account_custom/pending_dc_report_xlsx?date_from=%s&date_to=%s'
                  % (self.date_from, self.date_to),
            'target': 'self',
        }

    def _get_delivery_date_for_line(self, line):
        """Return the most recent done delivery date for this SO line."""
        if not line.move_ids:
            return line.order_id.date_order.date() if line.order_id.date_order else None
        pickings = line.move_ids.mapped('picking_id').filtered(lambda p: p.state == 'done' and p.date_done)
        if not pickings:
            return line.order_id.date_order.date() if line.order_id.date_order else None
        return max(pickings.mapped('date_done')).date()

    def _get_tracking_number(self, line):
        """Return tracking/reference number (delivery order or sale order name)."""
        if line.move_ids:
            pickings = line.move_ids.mapped('picking_id')
            if pickings:
                return pickings[0].name or ''
        return line.order_id.name or ''

    def _get_invoice_date_for_line(self, line):
        """Return the most recent posted invoice date for this SO line."""
        inv_lines = line.invoice_lines.filtered(
            lambda l: l.move_id.state == 'posted'
        )
        if not inv_lines:
            return line.order_id.date_order.date() if line.order_id.date_order else None
        return max(inv_lines.mapped('move_id.invoice_date'))

    def get_report_data(self):
        """
        Build data for Sales Bills Pending report:
        - Section 1: Goods Delivered but Bills not Made (delivered > invoiced)
        - Section 2: Bills Made but Goods not Delivered (invoiced > delivered)
        """
        self.ensure_one()
        SaleOrderLine = self.env['sale.order.line']
        precision = SaleOrderLine._fields['product_uom_qty'].get_digits(self.env)[1]
        precision = precision or 2

        domain = [
            ('order_id.state', 'in', ('sale', 'done')),
            ('order_id.company_id', '=', self.env.company.id),
            ('display_type', '=', False),
            ('product_id', '!=', False),
        ]
        # Filter by order date in range (date_order is datetime)
        domain += [
            ('order_id.date_order', '>=', datetime.combine(self.date_from, time.min)),
            ('order_id.date_order', '<=', datetime.combine(self.date_to, time.max)),
        ]
        lines = SaleOrderLine.search(domain, order='order_id, id')
        lines = lines.sorted(key=lambda l: (l.order_id.date_order or datetime.min, l.id))

        goods_delivered_not_billed = []
        bills_made_not_delivered = []
        total_bills_not_delivered_value = 0.0

        for line in lines:
            qty_del = line.qty_delivered or 0.0
            qty_inv = line.qty_invoiced or 0.0
            pending_delivered = qty_del - qty_inv
            pending_not_delivered = qty_inv - qty_del

            if float_compare(pending_delivered, 0, precision_digits=precision) > 0:
                # Goods Delivered but Bills not Made
                delivery_date = self._get_delivery_date_for_line(line)
                date_str = delivery_date.strftime('%d-%b-%y') if delivery_date else ''
                uom = line.product_uom.name if line.product_uom else 'Pcs'
                goods_delivered_not_billed.append({
                    'date_str': date_str,
                    'tracking_number': self._get_tracking_number(line),
                    'party_name': line.order_id.partner_id.name or '',
                    'item_name': line.name or (line.product_id.display_name or ''),
                    'initial_qty': qty_del,
                    'pending_qty': pending_delivered,
                    'uom': uom,
                    'rate': None,
                    'discount': None,
                    'value': None,
                })

            if float_compare(pending_not_delivered, 0, precision_digits=precision) > 0:
                # Bills Made but Goods not Delivered
                inv_date = self._get_invoice_date_for_line(line)
                date_str = inv_date.strftime('%d-%b-%y') if inv_date else ''
                uom = line.product_uom.name if line.product_uom else 'Pcs'
                price = line.price_unit or 0.0
                discount = line.discount or 0.0
                # Value for pending (not delivered) = pending qty * price after discount
                price_after_discount = price * (1 - (discount / 100.0))
                value = -(pending_not_delivered * price_after_discount)
                total_bills_not_delivered_value += abs(value)
                bills_made_not_delivered.append({
                    'date_str': date_str,
                    'tracking_number': self._get_tracking_number(line),
                    'party_name': line.order_id.partner_id.name or '',
                    'item_name': line.name or (line.product_id.display_name or ''),
                    'initial_qty': qty_inv,
                    'pending_qty': -pending_not_delivered,
                    'uom': uom,
                    'rate': price,
                    'discount': discount,
                    'value': value,
                })

        company = self.env.company
        date_from_str = self.date_from.strftime('%d-%b-%y') if self.date_from else ''
        date_to_str = self.date_to.strftime('%d-%b-%y') if self.date_to else ''

        return {
            'company_name': company.name,
            'company_street': company.street or '',
            'company_street2': company.street2 or '',
            'company_city': company.city or '',
            'company_state': company.state_id.name if company.state_id else '',
            'company_zip': company.zip or '',
            'company_country': company.country_id.name if company.country_id else '',
            'company_cin': getattr(company, 'cin', None) or '',
            'date_from_str': date_from_str,
            'date_to_str': date_to_str,
            'goods_delivered_not_billed': goods_delivered_not_billed,
            'bills_made_not_delivered': bills_made_not_delivered,
            'total_bills_not_delivered_value': total_bills_not_delivered_value,
        }
