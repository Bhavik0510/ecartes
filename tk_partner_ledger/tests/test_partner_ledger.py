# -*- coding: utf-8 -*-
import re
from datetime import date
from odoo.tests.common import TransactionCase, tagged


@tagged('test_partner_ledger')
class TestPartnerLedger(TransactionCase):
    """
        Test case for the 'PartnerLedger' model.
        This test suite checks the functionality of the customer ledger process.
    """

    @classmethod
    def setUpClass(cls):
        """
                Set up the test class by creating a partner with an initial approval state of
                'draft'.
        """
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test.partner@example.com',
        })
        cls.invoice = cls.env['account.move'].create({
            'partner_id': cls.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': date(2025, 1, 1),
            'amount_total': 100.0,
        })
        cls.payment = cls.env['account.payment'].create({
            'partner_id': cls.partner.id,
            'date': date(2025, 1, 15),
            'amount': 50.0,
        })
        cls.wizard = cls.env['partner.ledger.report'].create({
            'partner_id': cls.partner.id,
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31),
        })

    def test_generate_pdf_report(self):
        """
        Test if the PDF report generation works as expected.
        """
        pdf_action = self.wizard.btn_pdf_action()
        self.assertEqual(pdf_action.get('type'), 'ir.actions.report')

    def test_generate_excel_report(self):
        """
        Test if the Excel report generation works as expected.
        """
        excel_action = self.wizard.btn_excel_action()

        self.assertTrue(excel_action.get('type') == 'ir.actions.act_url')
        self.assertIn('/web/content/', excel_action.get('url'))

        pattern = r'/web/content/(\d+)\?download=true'
        match = re.search(pattern, excel_action.get('url'))

        if match:
            extracted_attachment_id = match.group(1)
            self.assertIsNotNone(extracted_attachment_id)
        else:
            self.fail("Attachment ID not found in the URL")

    def test_action_open_wizard_ledger(self):
        """
        Test if the partner's ledger wizard can be opened correctly.
        """
        action = self.partner.action_open_wizard_ledger()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertIn('context', action)
        self.assertEqual(action.get('res_model'), 'partner.ledger.report')
        self.assertEqual(action.get('view_mode'), 'form')

    def test_invoice_and_payment_both_sides(self):
        """
        Test that both Invoice (Debit) and Payment (Credit) entries
        appear in the Partner Ledger report combined data.
        """
        receivable_account = self.partner.property_account_receivable_id
        company = self.env.company
        revenue_account = self.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [company.id]),
        ], limit=1)
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', company.id),
        ], limit=1)

        # 1. Create and post an Invoice (Debit to Receivable)
        invoice = self.env['account.move'].create({
            'partner_id': self.partner.id,
            'move_type': 'out_invoice',
            'invoice_date': date(2025, 1, 10),
            'date': date(2025, 1, 10),
            'invoice_line_ids': [(0, 0, {
                'name': 'Service charge',
                'account_id': revenue_account.id if revenue_account else False,
                'price_unit': 1000.0,
                'quantity': 1,
            })],
        })
        invoice.action_post()

        # 2. Create and post a Payment entry (Credit to Receivable)
        payment_move = self.env['account.move'].create({
            'journal_id': bank_journal.id,
            'date': date(2025, 1, 20),
            'line_ids': [
                (0, 0, {
                    'account_id': bank_journal.default_account_id.id,
                    'name': 'Bank Inflow',
                    'debit': 600.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': receivable_account.id,
                    'partner_id': self.partner.id,
                    'name': 'Customer Payment / Receipt',
                    'debit': 0.0,
                    'credit': 600.0,
                }),
            ],
        })
        payment_move.action_post()

        # 3. Retrieve report values
        report_model = self.env['report.tk_partner_ledger.report_partner_ledger_pdf']
        report_values = report_model._get_report_values(
            self.wizard.ids,
            data={
                'partner_id': self.partner.id,
                'form_data': {
                    'start_date': date(2025, 1, 1),
                    'end_date': date(2025, 1, 31),
                }
            }
        )

        invoices = report_values.get('invoices', [])
        payments = report_values.get('payments', [])
        combined_data = report_values.get('combined_data', [])

        self.assertTrue(len(invoices) >= 1, "Invoice side should have at least 1 record")
        self.assertTrue(len(payments) >= 1, "Payment side should have at least 1 record")
        self.assertEqual(invoices[0]['amount'], 1000.0)
        self.assertEqual(payments[0]['amount'], 600.0)
        self.assertTrue(any(row.get('invoice_amount') == 1000.0 for row in combined_data))
        self.assertTrue(any(row.get('payment_amount') == 600.0 for row in combined_data))

