{
    "name" : "ecartes_business trip",
    "version" : "15.0",
    "category": "Uncategorized",
    "summary": "ecartes_business trip",
    "description": "ecartes_business trip",
    "depends": ['base','hr_holidays','hr','web_notify'],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "Data/leave_type.xml",
        "Data/mail_data.xml",
        "views/business_trip.xml",
        # "views/hr_employee.xml",
        "views/Inherit_hr_leave_type.xml",

    ],
    'license': 'LGPL-3',
}
