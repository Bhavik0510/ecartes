from odoo import fields, models


class AccountItemLedger(models.TransientModel):
    """Item Ledger wizard - select item and date range."""

    _name = 'account.item.ledger'
    _description = 'Item Ledger'

    product_id = fields.Many2one(
        'product.product',
        string='Item / Product',
        help='Leave empty for all items.',
    )
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

    def action_print_pdf(self):
        """Generate Stock Item Ledger PDF report. Requires Item/Product to be selected."""
        self.ensure_one()
        if not self.product_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Product Required',
                    'message': 'Please select an Item / Product to generate the PDF report.',
                    'type': 'warning',
                    'sticky': False,
                },
            }
        return self.env.ref('arclight_account_custom.action_print_item_ledger').report_action(self)

    def get_report_lines(self):
        """Build Stock Item Ledger data for PDF: report_lines, product_name, date_from_str, date_to_str."""
        self.ensure_one()
        empty = {
            'report_lines': [],
            'product_name': '',
            'date_from_str': '',
            'date_to_str': '',
        }
        if not self.product_id:
            return empty
        move_domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')),
            ('state', '=', 'posted'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', 'in', self.env.companies.ids),
        ]
        moves = self.env['account.move'].search(move_domain, order='date, id')
        lines = self.env['account.move.line']
        for move in moves:
            if not move.invoice_line_ids:
                continue
            matching = move.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and l.product_id == self.product_id
            )
            lines |= matching
        lines = lines.sorted(key=lambda l: (l.date, l.id))
        rows = []
        running_qty = 0.0
        running_value = 0.0
        for line in lines:
            move = line.move_id
            qty = abs(line.quantity or 0.0)
            rate = line.price_unit or 0.0
            value = line.price_subtotal or 0.0
            if value and not qty:
                qty = 1.0
            in_qty = in_rate = in_value = 0.0
            out_qty = out_rate = out_value = 0.0
            if move.move_type == 'in_invoice':
                in_qty, in_rate, in_value = qty, rate, value
            elif move.move_type == 'in_refund':
                out_qty, out_rate, out_value = qty, rate, abs(value)
            elif move.move_type == 'out_invoice':
                out_qty, out_rate, out_value = qty, rate, abs(value)
            elif move.move_type == 'out_refund':
                in_qty, in_rate, in_value = qty, rate, abs(value)
            vch_type = 'GST Purchase' if move.move_type == 'in_invoice' else \
                       'Purchase Return' if move.move_type == 'in_refund' else \
                       'GST-TAX INVOICE' if move.move_type == 'out_invoice' else 'Sales Return'
            if in_qty or in_value:
                running_qty += in_qty
                running_value += in_value
            if out_qty or out_value:
                avg_rate = (running_value / running_qty) if running_qty else 0.0
                running_value -= out_qty * avg_rate
                running_qty -= out_qty
                if running_qty < 0:
                    running_qty, running_value = 0.0, 0.0
            close_rate = (running_value / running_qty) if running_qty else 0.0
            date_str = line.date.strftime('%d-%b-%y') if line.date else ''
            partner_name = move.partner_id.sudo().name if move.partner_id else ''
            rows.append({
                'date_str': date_str,
                'particulars': partner_name or '',
                'vch_type': vch_type,
                'vch_no': move.name or move.ref or '',
                'in_qty': in_qty, 'in_rate': in_rate, 'in_value': in_value,
                'out_qty': out_qty, 'out_rate': out_rate, 'out_value': out_value,
                'close_qty': running_qty, 'close_rate': close_rate, 'close_value': running_value,
            })
        product_name = self.product_id.sudo().display_name if self.product_id else ''
        date_from_str = self.date_from.strftime('%d-%b-%y') if self.date_from else ''
        date_to_str = self.date_to.strftime('%d-%b-%y') if self.date_to else ''
        return {
            'report_lines': rows,
            'product_name': product_name,
            'date_from_str': date_from_str,
            'date_to_str': date_to_str,
        }

