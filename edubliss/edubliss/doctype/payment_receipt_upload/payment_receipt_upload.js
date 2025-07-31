// Copyright (c) 2025, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Receipt Upload", {
	refresh(frm) {
        // Clear value_addition_item field for all rows if form is new
        // if (frm.is_new()) {
        //     (frm.doc.expenses || []).forEach(function(row) {
        //         frappe.model.set_value(row.doctype, row.name, 'value_addition_item', '');
        //     });
        // }

	},

    setup(frm) {
        const me = this;
        
        // Set up query for billing document field
        frm.fields_dict.billing_receipts.grid.get_field("billing_document").get_query = function(doc, cdt, cdn) {
            const d = locals[cdt][cdn];
            const filters = [
                [d.billing_document_type, "docstatus", "=", "1"]
            ];

            // Additional filter for Purchase Invoices
            if (d.billing_document_type === "Sales Invoice") {
                filters.push(["Sales Invoice", "outstanding_amount", ">", "0"]);
            }

            return { filters: filters };
        };

        // Set up field mappings
        frm.add_fetch("billing_document", "student", "student");
        frm.add_fetch("billing_document", "posting_date", "posting_date");
        frm.add_fetch("billing_document", "outstanding_amount", "outstanding");
        frm.add_fetch("billing_document", "base_grand_total", "grand_total");
    }
});