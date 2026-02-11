# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
import logging
import requests
_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_type = fields.Selection(
        selection_add=[('Permanent', 'Permanent')],
        string='Employee Type',
        ondelete={'Permanent': 'cascade'}
    )
    woco_id = fields.Char(string="WoCo Id")
    woco_emp_id = fields.Char(string="Employee Id")

    @api.model
    def cron_sync_employee_woco(self):
        def convert_dob(dob_str):
            try:
                start_date = datetime(1970, 1, 1)
                return start_date + timedelta(days=int(dob_str))
            except Exception as e:
                return False

        def get_record_id(object_name, record_name):
            rec_ids = self.env[object_name].search_read([('name', '=', record_name)], ['id'])
            if not rec_ids:
                rec_ids = self.env[object_name].create({'name': record_name})
            return rec_ids[0]['id'] if rec_ids else False

        hr_emp_obj = self.env['hr.employee']
        for employee in self.get_employee_data()['data']:
            vals = {
                'name': f"{employee['fname']} {employee['lname']}",  # Full name
                'mobile_phone': employee['mobile'],  # Mobile number
                'gender': employee['gender'].lower(),  # Gender
                'birthday': convert_dob(employee['dob']),  # Convert to date
                'marital': employee['marital_status'].lower(),  # Marital status
                # 'address_home_id': {
                #     'street': employee['address_line_1'],
                #     'street2': employee['address_line_2'],
                #     'city': employee['city'],
                #     'state_id': employee['state'],
                #     'zip': employee['zip'],
                #     'country_id': employee['nationality'] or employee['country'],
                # },
                'woco_emp_id': employee['emp_id'],
                'department_id': get_record_id('hr.department', employee['department']),
                'job_id': get_record_id('hr.job', employee['designation']),
                'employee_type': employee['employee_type'],  # Employment type
                'work_email': employee['email'],  # Work email (same as personal here)
                # 'joining_date': employee['joining_date'],  # Joining date
                'woco_id': employee['user_id'],
                'emergency_contact': employee['emergency_contacts']
            }
            emp = hr_emp_obj.search([('woco_emp_id', '=', employee['emp_id'])])
            try:
                if not emp:
                    hr_emp_obj.create([vals])
                else:
                    emp.write(vals)
            except Exception as e:
                _logger.exception(f"Creating Employee: {e}")

    @api.model
    def get_employee_data(self):
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('woco.woco_url')
            accesstoken = self.env['ir.config_parameter'].sudo().get_param('woco.woco_accesstoken')
            authorization = self.env['ir.config_parameter'].sudo().get_param('woco.woco_authorization')
            response = requests.get(url, headers={
                'accesstoken': accesstoken, 'Authorization': authorization},
                data={})
            response.raise_for_status()
            response = response.json()
            return response
        except Exception as e:
            _logger.exception(f"Fetching From WoCo: {e}")


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    woco_id = fields.Char()
    woco_emp_id = fields.Char()
