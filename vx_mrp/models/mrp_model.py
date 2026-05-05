from odoo import models, fields, api, _


class Manufacture(models.Model):
    _inherit = "mrp.production"
    _order = 'date_start desc'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not orderby and groupby:
            groupby_fields = groupby if isinstance(groupby, list) else [groupby]
            first_group_field = groupby_fields[0].split(':')[0]
            orderby = f'{first_group_field} desc'

        return super().read_group(
            domain, fields, groupby,
            offset=offset, limit=limit,
            orderby=orderby, lazy=lazy
        )
