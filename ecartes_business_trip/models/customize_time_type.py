
from odoo import models, fields, api


class AddBusinessTrip(models.Model):

    _inherit='hr.leave.type'

    # time_type=fields.Selection(selection_add=[('business_trip','Business Trip')])
    is_business_trip=fields.Boolean('Is Business Trip:')
