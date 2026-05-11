{
    "name": "Ecartes: Company switcher without branch cascade",
    "summary": "Selecting a parent company does not auto-select child companies in the systray menu.",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "ecartes_switch_company/static/src/js/switch_company_no_branch_cascade.js",
        ],
    },
    "installable": True,
}
