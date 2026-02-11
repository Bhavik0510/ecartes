# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2023-Today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
{
    'name': "TCS & TDS in Indian Taxation System",
    'author': "AppsComp",
    'category': "Accounting",
    'summary': """TDS (Tax Deducted at Source) and TCS (Tax Collected at Source) are key components of the Indian taxation system. TDS involves deducting tax at the source of income, applicable to various earnings like salaries, interest, and payments to contractors. On the other hand, TCS requires sellers to collect a percentage of the sales value as tax from buyers at the time of sale. Both mechanisms are designed to ensure efficient tax collection and prevent tax evasion in India. """,
    'website': "http://www.asceticbs.com",
    'description': """TCS and TDS Management: Simplifying Tax Calculations for Indian Companies""",
    'version': '18.0.1.0',
    'price': 57.50,
    #'price': 47.75,
    'currency': 'EUR',
    'depends': ['base', 'account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_partner_inherited.xml',
        'views/account_move_inherited.xml',
        'views/res_config_view.xml',
        'views/tds_accounting.xml',

    ],
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    #'images': ['static/description/TCS TDS.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,

}
