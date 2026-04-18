{
    "name" : "ecartes_account",
    "version": "18.0.1.2",
    "category": "Uncategorized",
    "summary": "ecartes_account",
    "description": "ecartes_account",
    "depends": ['account', 'crm', 'sale', 'ecartes_contact'],
    "data": [
        "views/account_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "assets": {
        "web.assets_backend": [
            (
                "after",
                "web/static/src/views/kanban/kanban_arch_parser.js",
                "ecartes_account/static/src/js/kanban_arch_parser_patch.js",
            ),
        ],
    },
    'license': 'LGPL-3',
}
