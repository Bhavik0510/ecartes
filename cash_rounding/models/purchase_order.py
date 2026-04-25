from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    invoice_cash_rounding_id = fields.Many2one(
        "account.cash.rounding",
        string="Cash Rounding Method",
        copy=False,
        default=lambda self: self.env['account.cash.rounding'].search(
            [('rounding_method', '=', 'HALF-UP')], limit=1
        ),
    )

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        if self.invoice_cash_rounding_id:
            vals["invoice_cash_rounding_id"] = self.invoice_cash_rounding_id.id
        return vals

    @api.depends(
        "order_line.price_subtotal",
        "currency_id",
        "company_id",
        "payment_term_id",
        "invoice_cash_rounding_id",
    )
    def _compute_amounts(self):
        AccountTax = self.env["account.tax"]
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
                cash_rounding=order.invoice_cash_rounding_id,
            )
            order.amount_untaxed = tax_totals["base_amount_currency"]
            order.amount_tax = tax_totals["tax_amount_currency"]
            order.amount_total = tax_totals["total_amount_currency"]

    @api.depends_context("lang")
    @api.depends(
        "order_line.price_subtotal",
        "currency_id",
        "company_id",
        "payment_term_id",
        "invoice_cash_rounding_id",
    )
    def _compute_tax_totals(self):
        AccountTax = self.env["account.tax"]
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
                cash_rounding=order.invoice_cash_rounding_id,
            )