from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def _get_activity_groups(self):
        """Skip / cleanup activities whose model is no longer in the registry.

        Prevents KeyError (e.g. 'pbg.details') when opening the web client if a
        module is not loaded but mail.activity records still exist.
        """
        activities = self.env["mail.activity"].search(
            [("user_id", "=", self.env.uid)]
        )
        missing_models = {
            activity.res_model
            for activity in activities
            if activity.res_model and activity.res_model not in self.env
        }
        if missing_models:
            self.env["mail.activity"].sudo().search([
                ("res_model", "in", list(missing_models)),
            ]).unlink()
        return super()._get_activity_groups()
