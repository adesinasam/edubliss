frappe.ui.form.on('Program Enrollment', {
    refresh: function (frm) {
        // Hide button when conditions are met
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status != "Acceptance Paid") {
            frm.page.btn_primary.hide();
        } else {
            // Show button when conditions are not met (optional)
            frm.page.btn_primary.show();
        }

        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Enquiry") {
            frm.add_custom_button(__("Form Paid"), function() {
                frm.events.show_confirmation(frm, "Form Paid");
            });
        }
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Form Paid") {
            frm.add_custom_button(__("Test Booked"), function() {
                frm.events.show_confirmation(frm, "Test Booked");
            });
        }
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Test Booked") {
            frm.add_custom_button(__("Test Done"), function() {
                frm.events.show_confirmation(frm, "Test Done");
            });
        }
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Test Done") {
            frm.add_custom_button(__("Letter Issued"), function() {
                frm.events.show_confirmation(frm, "Letter Issued");
            });
        }
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Letter Issued") {
            frm.add_custom_button(__("Offer Accepted"), function() {
                frm.events.show_confirmation(frm, "Offer Accepted");
            });
            frm.add_custom_button(__("Offer Rejected"), function() {
                frm.events.show_confirmation(frm, "Offer Rejected");
            });
        }
        if (frm.doc.custom_is_transfer && frm.doc.custom_admission_status === "Offer Accepted") {
            frm.add_custom_button(__("Acceptance Paid"), function() {
                frm.events.show_confirmation(frm, "Acceptance Paid");
            });
        }
    },
    
    show_confirmation: function(frm, target_status) {
        const message = __("Are you sure you want to change the status to {0}?", [target_status]);
        
        frappe.confirm(
            message,
            function() {
                // Yes - proceed
                frm.events.progress(frm, target_status);
            },
            function() {
                // No - cancel
            },
            __("Confirm Status Change"),
            __("Proceed")
        );
    },
    
    progress: function(frm, target_status) {
        frappe.call({
            method: "edubliss.api.enquiry_progress",
            args: {
                "doctype": "Program Enrollment",
                "name": frm.doc.name,
                "target_status": target_status
            },
            callback: function(r) {
                if(!r.exc) {
                    frappe.show_alert({
                        message: __("Status changed to {0}", [target_status]),
                        indicator: 'green'
                    }, 5);
                    frm.reload_doc();
                }
            }
        });
    }
});