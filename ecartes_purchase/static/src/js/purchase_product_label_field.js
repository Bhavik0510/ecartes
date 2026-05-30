/** @odoo-module **/

import { ProductLabelSectionAndNoteField } from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";
import { registry } from "@web/core/registry";

export class EcartesPurchaseProductLabelField extends ProductLabelSectionAndNoteField {
    static template = "ecartes_purchase.ProductLabelSectionAndNoteField";

    get labelIsReadonly() {
        if (this.props.record.data.can_edit_po_desc) {
            return false;
        }
        if (this.props.readonly && this.isProductClickable && !this.isSectionOrNote) {
            return true;
        }
        return this.sectionAndNoteIsReadonly;
    }
}

export const ecartesPurchaseProductLabelField = {
    ...registry.category("fields").get("product_label_section_and_note_field"),
    component: EcartesPurchaseProductLabelField,
};

registry
    .category("fields")
    .add("ecartes_purchase_product_label_field", ecartesPurchaseProductLabelField);
