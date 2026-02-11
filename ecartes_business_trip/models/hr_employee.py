from odoo import _, api, fields, models


class HrEmployeeBusinessTrip(models.Model):
    _inherit = 'hr.employee'

    # business_trip_ = fields.Boolean(compute='_compute_business_trip_leave1',
    #                                string="Business Trip")
    # business_trip_string = fields.Char(string="Business Trip")
    #
    #
    # def _compute_business_trip_leave1(self):
    #     self.business_trip_ = False
    #     self.business_trip_string = False
    #     holidays = self.env['business.trip'].sudo().search([
    #         ('employee_id', 'in', self.ids),
    #         ('request_date_from', '<=', fields.Datetime.now()),
    #         ('request_date_to', '>=', fields.Datetime.now())
    #     ])
    #     for holiday in holidays:
    #         print("\n\nholidays:::::",holiday)
    #         employee = self.filtered(lambda e: e.id == holiday.employee_id.id)
    #         employee.business_trip_ = True
    #         employee.business_trip_string = "Business Trip"



