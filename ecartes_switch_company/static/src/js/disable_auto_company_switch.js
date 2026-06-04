import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

/** @odoo-module **/

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        
        // Intercept companyService for this FormController instance
        const originalCompanyService = this.companyService;
        this.companyService = Object.create(originalCompanyService);
        
        // Override setCompanies to prevent branch cascade
        this.companyService.setCompanies = (companyIds, includeChildCompanies) => {
            // Odoo's default FormController passes true for includeChildCompanies,
            // which causes all branch companies to be auto-selected when resolving AccessError.
            // We force it to false so it only selects the required company without its branches.
            return originalCompanyService.setCompanies(companyIds, false);
        };
    }
});
