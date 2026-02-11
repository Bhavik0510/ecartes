# -*- coding: utf-8 -*-
{
    'name': "ecartes_report",

    'summary': """
       ecartes_report""",

    'description': """
        ecartes_report
    """,
    'version': '15.0.1',
    'author': 'Tecblic Private Limited',
    'company': 'Tecblic Private Limited',
    'website': 'https://www.tecblic.com',
    'category': 'Uncategorized',
    'depends': ['base','sale','web','account','l10n_in','l10n_in_sale', 'ecartes_amc', 'purchase_stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/paper_format.xml',
        'data/ecartes_custom_report_template.xml',
        'data/document_tax_totals_report_inherit.xml',
        # 'data/tax_groups_total_inherit.xml',

        'reports/delhi_custom_header.xml',
        'reports/sale_order_report_template_inherit.xml',
        'reports/account_move.xml',
        'reports/proforma_invoice_report.xml',
        'reports/invoice_delivery_challan.xml',
        'reports/account_report.xml',
        'reports/invoice_slip_template.xml',
        'reports/amc_reports.xml',
        'reports/camc_reports.xml',
        'reports/purchase_order_report_template_inherit.xml',

        # 'reports/sale_report.xml',
        # 'reports/budgetary_quotation_government_template.xml',
        # 'reports/budgetary_quotation_printer_template.xml',
        # 'reports/ecartes_quote_india_report.xml',
        # 'reports/ecartes_quote_india_report_call.xml',
        # 'reports/ecartes_quote_mumbai_report_call.xml',
        # 'reports/ecartes_quote_mumbai_report.xml',
        # 'reports/ecartes_quote_usd_report.xml',
        # 'reports/ecartes_quote_usd_report_call.xml',
        
        # 'reports/invoice_mumbai_report.xml',
        # 'reports/invoice_usd.xml',
        'reports/mumbai_custom_header.xml',
        # 'reports/delivery_slip.xml',
        'reports/invoices.xml',
        'reports/report_picking_inherit.xml',
    ],
    'license': 'LGPL-3',
}

