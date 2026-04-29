from odoo import api, fields, models
from datetime import timedelta
from collections import defaultdict
from datetime import datetime, date
import logging
_logger = logging.getLogger(__name__)


class MarvexPartnerLedger(models.Model):
    _name = "marvex.partner.ledger"
    _description = "Marvex Partner Ledger"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer'
    )

    # def _check_date_in_range(self, check_date, from_date, to_date):
    #     """Helper function to check if date falls in range (handles both normal and swapped formats)"""
    #     # Check 1: Normal format
    #     if from_date <= check_date <= to_date:
    #         return True
    #
    #     # Check 2: Swapped format (day-month swap)
    #     try:
    #         corrected_date = date(check_date.year, check_date.day, check_date.month)
    #         if from_date <= corrected_date <= to_date:
    #             return True
    #     except ValueError:
    #         pass
    #
    #     return False

    def _compute_balance_as_of_date(self, as_of_date):
        """
        Compute opening balance as of (before) as_of_date using the SAME logic
        as the period (invoices, payments, containers, bulk, manual, TDS, etc.).
        So next year opening = this year closing.
        Returns (running_balance, opening_sent_amount).
        """
        self.ensure_one()
        receivable_account = self.partner_id.property_account_receivable_id
        company = self.env.company

        tds_payable_account = self.env["account.account"].search([
            ("company_ids", "in", [company.id]),
            ("code", "=", "112390"),
        ], limit=1)
        tds_receivable_account = self.env["account.account"].search([
            ("company_ids", "in", [company.id]),
            ("code", "=", "100580"),
        ], limit=1)

        # Same data sources as period but before as_of_date. Include by both line date
        # and move date so no entry is missed (e.g. move posted in 2024 with line date in range).
        all_move_lines = self.env["account.move.line"].search([
            ("partner_id", "=", self.partner_id.id),
            ("account_id", "=", receivable_account.id),
            ("move_id.state", "=", "posted"),
            ("move_id.company_id", "=", company.id),
            "|",
            ("date", "<", as_of_date),
            ("move_id.date", "<", as_of_date),
        ], order="date asc, id asc")

        # Bulk payment containers are only used if the model exists
        if "bulk.payment.container" in self.env:
            Container = self.env["bulk.payment.container"]
            all_containers = Container.search([
                ("partner_id", "=", self.partner_id.id),
                ("date", "<", as_of_date),
            ], order="date asc, id asc")
        else:
            all_containers = self.env["account.payment"]

        # Collect payment_ids only if the container model actually has that field
        container_payment_ids = []
        if all_containers and "payment_ids" in all_containers._fields:
            container_payment_ids = all_containers.mapped("payment_ids").ids
        excluded_payment_ids = list(set(container_payment_ids))

        manual_payments = self.env["account.payment"].search([
            ("partner_id", "=", self.partner_id.id),
            ("date", "<", as_of_date),
            ("payment_type", "=", "inbound"),
            ("state", "in", ("in_process", "paid")),
            ("id", "not in", excluded_payment_ids),
        ], order="date asc, id asc")
        manual_outbound_payments = self.env["account.payment"].search([
            ("partner_id", "=", self.partner_id.id),
            ("date", "<", as_of_date),
            ("payment_type", "=", "outbound"),
            ("state", "in", ("in_process", "paid")),
            ("id", "not in", excluded_payment_ids),
        ], order="date asc, id asc")

        tds_move_lines = self.env["account.move.line"].browse()
        if tds_payable_account:
            tds_move_lines = self.env["account.move.line"].search([
                ("partner_id", "=", self.partner_id.id),
                ("account_id", "=", tds_payable_account.id),
                ("move_id.state", "=", "posted"),
                ("date", "<", as_of_date),
            ], order="date asc, id asc")
        tds_receivable_move_lines = self.env["account.move.line"].browse()
        if tds_receivable_account:
            tds_receivable_move_lines = self.env["account.move.line"].search([
                ("partner_id", "=", self.partner_id.id),
                ("account_id", "=", tds_receivable_account.id),
                ("move_id.state", "=", "posted"),
                ("date", "<", as_of_date),
            ], order="date asc, id asc")

        move_dates = set(all_move_lines.mapped("date"))
        container_dates = set(all_containers.mapped("date"))
        manual_payment_dates = set(manual_payments.mapped("date"))
        manual_outbound_dates = set(manual_outbound_payments.mapped("date"))
        tds_dates = set(tds_move_lines.mapped("date")) if tds_move_lines else set()
        tds_rec_dates = set(tds_receivable_move_lines.mapped("date")) if tds_receivable_move_lines else set()

        all_dates = sorted(
            move_dates.union(container_dates)
            .union(manual_payment_dates).union(manual_outbound_dates)
            .union(tds_dates).union(tds_rec_dates)
        )
        # Only process dates before as_of_date (opening = balance before this date)
        all_dates = [d for d in all_dates if d < as_of_date]

        running_balance = 0.0

        for current_date in all_dates:
            # Invoices (out_invoice)
            invoice_lines = all_move_lines.filtered(
                lambda r: r.date == current_date and r.move_id.move_type == "out_invoice"
            )
            for inv in invoice_lines:
                running_balance += inv.debit
                if inv.move_id.reversal_move_ids:
                    for rv_inv in inv.move_id.reversal_move_ids:
                        running_balance -= rv_inv.amount_total

            # Journal (journal_id=3)
            journal = self.env["account.move"].search([
                ("date", "=", current_date),
                ("journal_id", "=", 3),
            ])
            journal_item = journal.filtered(
                lambda r: any(line.partner_id.id == self.partner_id.id for line in r.line_ids)
            )
            for item in journal_item:
                if tds_payable_account and any(line.account_id == tds_payable_account for line in item.line_ids):
                    continue
                if tds_receivable_account and any(line.account_id == tds_receivable_account for line in item.line_ids):
                    continue
                jl = item.invoice_line_ids.filtered(lambda x: x.partner_id) if item.invoice_line_ids else self.env["account.move.line"]
                for j in jl:
                    if j.debit > 1:
                        running_balance -= j.debit
                    if j.credit > 1:
                        running_balance += j.credit

            # Containers
            containers = all_containers.filtered(lambda c: c.date == current_date)
            if containers:
                for cont in containers:
                    container_credit = 0.0
                    for pay in cont.payment_ids:
                        container_credit += pay.amount if pay.payment_type == "inbound" else -pay.amount
                    if container_credit >= 0:
                        running_balance -= container_credit
                    else:
                        running_balance += abs(container_credit)
            # Note: bulk payments are intentionally ignored in opening balance

            # Manual payments
            for pay in manual_payments.filtered(lambda p: p.date == current_date):
                running_balance -= pay.amount
            for pay in manual_outbound_payments.filtered(lambda p: p.date == current_date):
                running_balance += pay.amount

            # Kasar
            kasar = self.env["account.move.line"].search([
                ("account_id.name", "=", "KASAR VATAV"),
                ("date", "=", current_date),
                ("partner_id", "=", self.partner_id.id),
            ])
            for k in kasar:
                if k.debit > 1:
                    running_balance -= k.debit
                if k.credit > 1:
                    running_balance += k.credit

            # TDS Payable 112390
            if tds_payable_account:
                for tds_line in tds_move_lines.filtered(lambda l: l.date == current_date):
                    if tds_line.credit > 0:
                        running_balance += tds_line.credit

            # TDS Receivable 100580
            if tds_receivable_account:
                for tds_rec_line in tds_receivable_move_lines.filtered(lambda l: l.date == current_date):
                    if tds_rec_line.debit > 0:
                        running_balance -= tds_rec_line.debit

        opening_sent_payments = self.env["account.payment"].search([
            ("partner_id", "=", self.partner_id.id),
            ("date", "<", as_of_date),
            ("payment_type", "=", "outbound"),
            ("state", "in", ("in_process", "paid")),
        ])
        opening_sent_amount = sum(opening_sent_payments.mapped("amount"))

        return (running_balance, opening_sent_amount)

    def get_updated_ledger_lines(self):
        self.ensure_one()
        lines = []
        receivable_account = self.partner_id.property_account_receivable_id

        debit_total = 0.0
        credit_total = 0.0
        jv_amount = 0.0

        # ---------------------------
        # OPENING BALANCE (from receivable move lines so 2023 payments etc. all included)
        # ---------------------------
        running_balance, opening_sent_amount = self._compute_balance_as_of_date(self.from_date)
        opening_balance = running_balance
        # Apply sent-amount logic for initial running_balance (same as before)
        if opening_balance < 0:
            running_balance = opening_balance + (2 * opening_sent_amount)
        elif opening_balance == 0 and opening_sent_amount:
            running_balance = opening_sent_amount
        else:
            running_balance = opening_balance

        # TDS Payable account 112390 - used for period lines
        tds_payable_account = self.env["account.account"].search([
            ("company_ids", "in", [self.env.company.id]),
            ("code", "=", "112390"),
        ], limit=1)

        # TDS Receivable account 100580 - used for period lines (credit side in partner ledger)
        tds_receivable_account = self.env["account.account"].search([
            ("company_ids", "in", [self.env.company.id]),
            ("code", "=", "100580"),
        ], limit=1)

        # ---------------------------
        # GET ALL LINES WITHIN RANGE
        # ---------------------------
        all_move_lines = self.env["account.move.line"].search([
            ("partner_id", "=", self.partner_id.id),
            ("account_id", "=", receivable_account.id),
            ("move_id.state", "=", "posted"),
            ("date", ">=", self.from_date),
            ("date", "<=", self.to_date),
        ], order="date asc, id asc")

        # ---------------------------
        # GET ALL CONTAINERS WITHIN RANGE
        # ---------------------------
        if "bulk.payment.container" in self.env:
            Container = self.env["bulk.payment.container"]
            all_containers = Container.search([
                ("partner_id", "=", self.partner_id.id),
                ("date", ">=", self.from_date),
                ("date", "<=", self.to_date),
            ], order="date asc, id asc")
        else:
            all_containers = self.env["account.payment"]

        # ---------------------------
        # BULK PAYMENTS ARE EXCLUDED FROM PARTNER LEDGER
        # (handled via underlying payments / accounting, not shown separately)
        # ---------------------------
        # from datetime import date

        # Year range માંથી બધા records લાવો
        # year_start = date(self.from_date.year, 1, 1)
        # year_end = date(self.to_date.year, 12, 31)
        #
        #
        # all_bulk_payments = BulkPayment.search([
        #     ("partner_id", "=", self.partner_id.id),
        #     ("date", ">=", year_start),
        #     ("date", "<=", year_end),
        #     ("state", "=", "received"),
        # ], order="id asc")
        #
        # # હવે filter કરો
        # filtered_payments = self.env['bulk.payment']
        # for payment in all_bulk_payments:
        #     payment_date = payment.date
        #
        #     # Check 1: Normal format
        #     if self.from_date <= payment_date <= self.to_date:
        #         filtered_payments |= payment
        #         continue
        #
        #     # Check 2: Swapped format
        #     try:
        #         corrected_date = date(payment_date.year,
        #                               payment_date.day,
        #                               payment_date.month)
        #
        #         if self.from_date <= corrected_date <= self.to_date:
        #             filtered_payments |= payment
        #         else:
        #             print(f"  ✗ Corrected date out of range: {self.from_date} to {self.to_date}")
        #     except ValueError as e:
        #         print(f"  ✗ Invalid date swap: {e}")
        #
        # print(f"\nFinal filtered records: {filtered_payments.ids}")

        # ======================================================
        # >>> ADDED LOGIC (MANUAL PAYMENTS – NOT BULK / CONTAINER)
        # ======================================================
        Payment = self.env['account.payment']

        container_payment_ids = []
        if all_containers and "payment_ids" in all_containers._fields:
            container_payment_ids = all_containers.mapped("payment_ids").ids

        excluded_payment_ids = list(set(container_payment_ids))

        manual_payments = Payment.search([
            ('partner_id', '=', self.partner_id.id),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ('in_process', 'paid')),
            # ('memo', '=', False),
            ('id', 'not in', excluded_payment_ids),
        ], order="date asc, id asc")

        # Manual OUTBOUND (send) payments - show in debit column in partner ledger
        manual_outbound_payments = Payment.search([
            ('partner_id', '=', self.partner_id.id),
            ('date', '>=', self.from_date),
            ('date', '<=', self.to_date),
            ('payment_type', '=', 'outbound'),
            ('state', 'in', ('in_process', 'paid')),
            ('id', 'not in', excluded_payment_ids),
        ], order="date asc, id asc")
        # ======================================================

        # ---------------------------
        # TDS Payable account 112390 - lines to show as "party pasethi levu" (credit → debit)
        # ---------------------------
        tds_move_lines = self.env["account.move.line"].browse()
        if tds_payable_account:
            tds_move_lines = self.env["account.move.line"].search([
                ("partner_id", "=", self.partner_id.id),
                ("account_id", "=", tds_payable_account.id),
                ("move_id.state", "=", "posted"),
                ("date", ">=", self.from_date),
                ("date", "<=", self.to_date),
            ], order="date asc, id asc")
        tds_dates = set(tds_move_lines.mapped("date")) if tds_move_lines else set()

        # ---------------------------
        # TDS Receivable account 100580 - lines to show as credit in partner ledger (debit in account → credit)
        # ---------------------------
        tds_receivable_move_lines = self.env["account.move.line"].browse()
        if tds_receivable_account:
            tds_receivable_move_lines = self.env["account.move.line"].search([
                ("partner_id", "=", self.partner_id.id),
                ("account_id", "=", tds_receivable_account.id),
                ("move_id.state", "=", "posted"),
                ("date", ">=", self.from_date),
                ("date", "<=", self.to_date),
            ], order="date asc, id asc")
        tds_receivable_dates = set(tds_receivable_move_lines.mapped("date")) if tds_receivable_move_lines else set()

        # ---------------------------
        # GET ALL UNIQUE DATES (from move lines, containers, bulk payments, manual, TDS 112390, TDS 100580)
        # ---------------------------
        move_dates = set(all_move_lines.mapped("date"))
        container_dates = set(all_containers.mapped("date"))
        manual_payment_dates = set(manual_payments.mapped("date"))
        manual_outbound_dates = set(manual_outbound_payments.mapped("date"))

        all_dates = sorted(
            move_dates.union(container_dates)
            .union(manual_payment_dates)
            .union(manual_outbound_dates)
            .union(tds_dates)
            .union(tds_receivable_dates)
        )
        credit_amount = 0
        # ---------------------------
        # PROCESS EACH DATE
        # ---------------------------
        for current_date in all_dates:

            # ======================================================

            # ------------------------------------------------------
            # STEP 2: THEN CHECK INVOICES FOR THIS DATE
            # ------------------------------------------------------
            invoice_lines = all_move_lines.filtered(
                lambda r: r.date == current_date and r.move_id.move_type in ['out_invoice']
            )

            for inv in invoice_lines:
                amount = inv.debit

                running_balance += amount
                debit_total += amount

                lines.append({
                    "date": current_date,
                    "narration": inv.move_id.ref or inv.move_id.name,
                    "book": "Invoice",
                    "debit": amount,
                    "credit": 0.0,
                    "running_balance": running_balance,
                })

                if inv.move_id.reversal_move_ids:
                    for rv_inv in inv.move_id.reversal_move_ids:
                        running_balance -= rv_inv.amount_total
                        lines.append({
                            "date": rv_inv.invoice_date,
                            "narration": rv_inv.ref or rv_inv.name,
                            "book": "CNT",
                            "debit": 0.0,
                            "credit": rv_inv.amount_total,
                            "running_balance": running_balance,
                        })
                    credit_amount += rv_inv.amount_total
                    credit_total += rv_inv.amount_total

            journal = self.env['account.move'].search([('date', '=', current_date),('journal_id','=',3)])
            journal_item = journal.filtered(lambda r: any(line.partner_id.id == self.partner_id.id for line in r.line_ids))
            for item in journal_item:
                if item:
                    # Skip entire move if it has 112390 (TDS Payable) - only TDS Payable block will show that as single debit
                    if tds_payable_account and any(line.account_id == tds_payable_account for line in item.line_ids):
                        continue
                    # Skip entire move if it has 100580 (TDS Receivable) - only TDS Receivable block will show that as single credit
                    if tds_receivable_account and any(line.account_id == tds_receivable_account for line in item.line_ids):
                        continue
                    jl = item.invoice_line_ids.filtered(lambda x: x.partner_id)
                    for j in jl:
                        if j.debit > 1:
                            running_balance -= j.debit
                            credit_total += j.debit
                            lines.append({
                                "date": current_date,
                                "narration": (j.name or '') + ' ' + (j.move_id.name or ''),
                                "book": "JV",
                                "debit": 0.0,
                                "credit": j.debit,
                                "running_balance": running_balance,
                            })
                            jv_amount += j.debit
                        if j.credit > 1:
                            running_balance += j.credit
                            debit_total += j.credit
                            lines.append({
                                "date": current_date,
                                "narration": (j.name or '') + ' ' + (j.move_id.name or ''),
                                "book": "JV",
                                "debit": j.credit,
                                "credit": 0.0,
                                "running_balance": running_balance,
                            })
                            jv_amount -= j.credit

            # ------------------------------------------------------
            # STEP 1: FIRST CHECK CONTAINERS FOR THIS DATE
            # ------------------------------------------------------
            containers = all_containers.filtered(lambda c: c.date == current_date)

            if containers:
                # Print separate line for each container (inbound = credit, outbound/send = debit)
                for cont in containers:
                    container_credit = 0.0
                    bank_number = None

                    # Sum payments in this specific container (inbound +, outbound -)
                    for pay in cont.payment_ids:
                        if pay.payment_type == "inbound":
                            container_credit += pay.amount
                        else:
                            container_credit -= pay.amount

                        # Get bank number for narration
                        if not bank_number and pay.partner_bank_id and pay.partner_bank_id.acc_number:
                            bank_number = pay.partner_bank_id.acc_number

                    narration_text = bank_number or "Receipt"

                    if container_credit >= 0:
                        # Net inbound: show as credit (received)
                        running_balance -= container_credit
                        credit_total += container_credit
                        lines.append({
                            "date": current_date,
                            "narration": narration_text,
                            "book": "Payment",
                            "debit": 0.0,
                            "credit": container_credit,
                            "running_balance": running_balance,
                        })
                    else:
                        # Net outbound (send): show as debit
                        debit_amt = abs(container_credit)
                        running_balance += debit_amt
                        debit_total += debit_amt
                        lines.append({
                            "date": current_date,
                            "narration": narration_text or "Send",
                            "book": "Payment",
                            "debit": debit_amt,
                            "credit": 0.0,
                            "running_balance": running_balance,
                        })
            # Note: bulk payments are intentionally ignored in partner ledger lines

            # ======================================================
            # >>> ADDED LOGIC (MANUAL PAYMENTS)
            # ======================================================
            manual_lines = manual_payments.filtered(lambda p: p.date == current_date)

            for pay in manual_lines:
                bank_number = (
                    pay.partner_bank_id.acc_number
                    if pay.partner_bank_id and pay.partner_bank_id.acc_number
                    else pay.journal_id.name
                )

                running_balance -= pay.amount
                credit_total += pay.amount

                lines.append({
                    "date": current_date,
                    "narration": bank_number or "Receipt",
                    "book": "Payment",
                    "debit": 0.0,
                    "credit": pay.amount,
                    "running_balance": running_balance,
                })

            # Manual OUTBOUND (send) payments - show in debit column
            manual_outbound_lines = manual_outbound_payments.filtered(lambda p: p.date == current_date)
            for pay in manual_outbound_lines:
                bank_number = (
                    pay.partner_bank_id.acc_number
                    if pay.partner_bank_id and pay.partner_bank_id.acc_number
                    else pay.journal_id.name
                )
                running_balance += pay.amount
                debit_total += pay.amount
                lines.append({
                    "date": current_date,
                    "narration": bank_number or "Send",
                    "book": "Payment",
                    "debit": pay.amount,
                    "credit": 0.0,
                    "running_balance": running_balance,
                })

            kasar = self.env['account.move.line'].search([('account_id.name', '=', 'KASAR VATAV'), ('date', '=', current_date),('partner_id','=',self.partner_id.id)])
            if kasar:
                if kasar.debit > 1:
                    running_balance -= kasar.debit
                    credit_total += kasar.debit
                    lines.append({
                        "date": current_date,
                        "narration": kasar.name or '',
                        "book": "kasar",
                        "debit": 0.0,
                        "credit": kasar.debit,
                        "running_balance": running_balance,
                    })
                    jv_amount += kasar.debit
                if kasar.credit > 1:
                    running_balance += kasar.credit
                    debit_total += kasar.credit
                    lines.append({
                        "date": current_date,
                        "narration": kasar.name or '',
                        "book": "kasar",
                        "debit": kasar.credit,
                        "credit": 0.0,
                        "running_balance": running_balance,
                    })
                    jv_amount -= kasar.credit

            # ------------------------------------------------------
            # TDS Payable 112390: credit → show as debit (party pasethi levu), debit → show as credit
            # Debit side entry: line show karo but closing/running_balance ma apavana (include na karo)
            # ------------------------------------------------------
            if tds_payable_account:
                tds_lines_date = tds_move_lines.filtered(lambda l: l.date == current_date)
                for tds_line in tds_lines_date:
                    narration_tds = (tds_line.move_id.ref or tds_line.move_id.name or tds_line.name or "TDS Payable")
                    if tds_line.credit > 0:
                        # Credit in 112390 = amount to receive from party → show in Debit column
                        running_balance += tds_line.credit
                        debit_total += tds_line.credit
                        lines.append({
                            "date": current_date,
                            "narration": narration_tds,
                            "book": "TDS Payable",
                            "debit": tds_line.credit,
                            "credit": 0.0,
                            "running_balance": running_balance,
                        })
                    if tds_line.debit > 0:
                        # Debit in 112390 → show in Credit column (entry show karo, but closing ma apavana)
                        lines.append({
                            "date": current_date,
                            "narration": narration_tds,
                            "book": "TDS Payable",
                            "debit": 0.0,
                            "credit": tds_line.debit,
                            "running_balance": running_balance,
                        })

            # ------------------------------------------------------
            # TDS Receivable 100580: debit → show as credit (party ne apvu - reduces receivable), credit → show as debit
            # TDS Payable jem j debit side, evi rite TDS Receivable credit side ave
            # ------------------------------------------------------
            if tds_receivable_account:
                tds_rec_lines_date = tds_receivable_move_lines.filtered(lambda l: l.date == current_date)
                for tds_rec_line in tds_rec_lines_date:
                    narration_tds_rec = (tds_rec_line.move_id.ref or tds_rec_line.move_id.name or tds_rec_line.name or "TDS Receivable")
                    if tds_rec_line.debit > 0:
                        # Debit in 112391 = TDS received from party → show in Credit column (reduces receivable)
                        running_balance -= tds_rec_line.debit
                        credit_total += tds_rec_line.debit
                        lines.append({
                            "date": current_date,
                            "narration": narration_tds_rec,
                            "book": "TDS Receivable",
                            "debit": 0.0,
                            "credit": tds_rec_line.debit,
                            "running_balance": running_balance,
                        })
                    if tds_rec_line.credit > 0:
                        # Credit in 112391 → show in Debit column (entry show karo, but closing ma apavana)
                        lines.append({
                            "date": current_date,
                            "narration": narration_tds_rec,
                            "book": "TDS Receivable",
                            "debit": tds_rec_line.credit,
                            "credit": 0.0,
                            "running_balance": running_balance,
                        })

        # ------------------------------------------------------
        # OPENING BALANCE - amount to collect (levanu baki) in Debit column
        # so next year report ma opening debit side ave
        # ------------------------------------------------------
        if opening_balance >= 0:
            opening_debit = opening_balance
            opening_credit = opening_sent_amount
        else:
            opening_debit = opening_sent_amount
            opening_credit = abs(opening_balance)

        # ------------------------------------------------------
        # CLOSING BALANCE - amount to receive (levanu baki) in Credit column
        # so last row grand total same thai (both sides equal)
        # Positive = amount to receive -> Credit; negative -> Debit
        # ------------------------------------------------------
        closing_balance_cf = running_balance
        if closing_balance_cf > 0:
            closing_debit = 0.0
            closing_credit = closing_balance_cf
        else:
            closing_debit = abs(closing_balance_cf)
            closing_credit = 0.0

        # ------------------------------------------------------
        # GRAND TOTALS - Should always match
        # ------------------------------------------------------
        grand_total_debit = opening_debit + debit_total + closing_debit
        grand_total_credit = opening_credit + credit_total + closing_credit

        # Closing amounts માટે
        # all_invoices = self.env['account.move'].search([
        #     ('partner_id', '=', self.partner_id.id)
        # ])
        #
        # closing_invoice_amount = 0
        # for inv in all_invoices:
        #     if inv.invoice_date:
        #         # Check if date is before to_date (using same swapped logic)
        #         if inv.invoice_date < self.to_date:
        #             closing_invoice_amount += inv.amount_total
        #         else:
        #             # Try swapped format
        #             try:
        #                 corrected = date(inv.invoice_date.year,
        #                                  inv.invoice_date.day,
        #                                  inv.invoice_date.month)
        #                 if corrected < self.to_date:
        #                     closing_invoice_amount += inv.amount_total
        #             except ValueError:
        #                 pass
        #
        # # Same for payments
        # all_payments = self.env['account.payment'].search([
        #     ('partner_id', '=', self.partner_id.id)
        # ])
        #
        # closing_payment_amount = 0
        # for pay in all_payments:
        #     if pay.date:
        #         if pay.date < self.to_date:
        #             closing_payment_amount += pay.amount
        #         else:
        #             try:
        #                 corrected = date(pay.date.year, pay.date.day, pay.date.month)
        #                 if corrected < self.to_date:
        #                     closing_payment_amount += pay.amount
        #             except ValueError:
        #                 pass
        #
        # closing_credit = closing_invoice_amount - closing_payment_amount - jv_amount

        return {
            "lines": lines,
            "debit_total": debit_total,
            "credit_total": credit_total,
            "opening_debit": opening_debit,
            "opening_credit": opening_credit,
            "closing_debit": closing_debit,
            "closing_credit": closing_credit,
            "grand_total_debit": grand_total_debit,
            "grand_total_credit": grand_total_credit,
        }

    def action_print(self):
        return self.env.ref('arclight_account_custom.action_partner_ledger_report').report_action(self)
