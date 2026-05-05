# -*- coding: utf-8 -*-
{
    "name": "Purchase Backdate",
    "summary": "Confirm and update purchase documents with backdate",
    "description": """
Allows setting purchase backdate and remarks, including mass assignment,
and propagates those values to receipts, stock moves, bills, and entries.
""",
    "version": "18.0.1.0.0",
    "author": "Softhealer Technologies",
    "category": "Purchase",
    "website": "https://softhealer.com",
    "license": "OPL-1",
    "depends": ["purchase", "stock", "account"],
    "data": [
        "security/sh_purchase_backdate_groups.xml",
        "security/ir.model.access.csv",
        "wizard/sh_purchase_backdate_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/stock_move_line_views.xml",
        "views/account_move_views.xml",
        "data/purchase_order_data.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
