
frappe.ui.form.on('Student', {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.customer) {
            frm.add_custom_button(__('Add Guardian as Portal User'), function() {
                frappe.call({
                    method: "edubliss.api.add_guardian_to_customer_portal",
                    args: {
                        "student_id": frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                        }
                        frm.reload_doc();
                    }
                });
            });
        }
    }
});