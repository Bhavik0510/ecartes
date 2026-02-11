# -*- coding: utf-8 -*-
#########################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2022-TODAY Kiran Infosoft. (<https://kiraninfosoft.com>).

#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version. You can not redistribute or sale
#    without permission of Kiran Infosoft. (<https://kiraninfosoft.com>).

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#########################################################################################
{
    'name': "GST Return Reports",
    'summary': """GST Return Reports""",
    'description': """
GSTR1 report for file on Indian Government Portal 

Indian Return File Process
GST
Indian GST
GSTR1 Report
    """,
    "version": "1.0",
    "category": "Accounting/Accounting",
    'author': "Kiran Infosoft",
    "website": "https://kiraninfosoft.com",
    'price': 90.0,
    'currency': 'EUR',
    "application": False,
    'installable': True,
    'images': ['static/description/gstr-ki.jpg'],
    "depends": [
        'l10n_in',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/gstr_return_view.xml',
    ],
    "license": "LGPL-3"
}
