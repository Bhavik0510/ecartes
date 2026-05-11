import { patch } from "@web/core/utils/patch";
import { CompanySelector } from "@web/webclient/switch_company_menu/switch_company_menu";

/** @odoo-module **/

patch(CompanySelector.prototype, {
    /**
     * Odoo default: selecting a company also selects all `child_ids` (branches).
     * Return no children so each company is toggled independently.
     */
    _getBranches() {
        return [];
    },
});
