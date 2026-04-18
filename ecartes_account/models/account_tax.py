from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _distribute_delta_amount_smoothly(self, precision_digits, delta_amount, target_factors):
        """Defensive guard for malformed tax repartition edge-cases.

        In some customer databases, tax repartition inputs can produce an empty
        normalized factor list while a delta still needs distribution, causing
        IndexError in the core implementation.
        """
        amounts_to_distribute = [0.0] * len(target_factors)
        if not target_factors:
            return amounts_to_distribute

        try:
            return super()._distribute_delta_amount_smoothly(
                precision_digits, delta_amount, target_factors
            )
        except IndexError:
            factors = self._normalize_target_factors(target_factors)
            if not factors:
                return amounts_to_distribute

            precision_rounding = float(f"1e-{precision_digits}")
            remaining_errors = round(abs(delta_amount / precision_rounding))
            sign = -1 if delta_amount < 0.0 else 1
            for idx in range(remaining_errors):
                amounts_to_distribute[factors[idx % len(factors)][0]] += sign * precision_rounding
            return amounts_to_distribute
