// Copyright (c) 2025, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Receipt Upload", {
	refresh(frm) {
        // Set user name if not set
        if (!frm.doc.user_name) {
            frm.set_value('user_name', frappe.session.user_fullname || frappe.session.user);
        }

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
    },

    validate: function(frm) {
        // Validate that total allocated amount equals paid amount
        let total_allocated = 0;
        $.each(frm.doc.billing_receipts || [], function(i, row) {
            total_allocated += flt(row.allocated_amount);
        });

        if (Math.abs(total_allocated - flt(frm.doc.paid_amount)) > 0.01) {
            frappe.throw(__('Total allocated amount ({0}) must equal paid amount ({1})', [total_allocated, frm.doc.paid_amount]));
        }

        // Validate reference_no and reference_date if mode_of_payment requires it
        if (frm.doc.mode_of_payment) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Mode of Payment',
                    filters: { name: frm.doc.mode_of_payment },
                    fieldname: ['type']
                },
                callback: function(r) {
                    if (r.message && r.message.type === 'Bank') {
                        if (!frm.doc.attach_image) {
                            frappe.throw(__('Please attach either an image for bank transactions'));
                        }
                        if (!frm.doc.reference_no || !frm.doc.reference_date) {
                            frappe.throw(__('Cheque/Reference No or Cheque/Reference Date cannot be empty'));
                        }
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Payment Receipt Details', {
    allocated_amount: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (row.allocated_amount > flt(row.outstanding)) {
            frappe.msgprint(__('Allocated amount cannot be greater than outstanding amount'));
            frappe.model.set_value(cdt, cdn, 'allocated_amount', row.outstanding);
        }
    }
});
