frappe.ui.form.on('Lead', {
    refresh: function (frm) {
        if (frm.doc.status === "Quotation" && frm.doc.custom_admission_status === "Acceptance Paid") {
            frm.add_custom_button(__("Create Student Applicant"), function() {
                frm.events.show_enroll_confirmation(frm);
            });
        }
        if (frm.doc.custom_admission_status === "Enquiry") {
            frm.add_custom_button(__("Form Paid"), function() {
                frm.events.show_confirmation(frm, "Form Paid");
            });
        }
        if (frm.doc.custom_admission_status === "Form Paid") {
            frm.add_custom_button(__("Test Booked"), function() {
                frm.events.show_confirmation(frm, "Test Booked");
            });
        }
        if (frm.doc.custom_admission_status === "Test Booked") {
            frm.add_custom_button(__("Test Done"), function() {
                frm.events.show_confirmation(frm, "Test Done");
            });
        }
        if (frm.doc.custom_admission_status === "Test Done") {
            frm.add_custom_button(__("Letter Issued"), function() {
                frm.events.show_confirmation(frm, "Letter Issued");
            });
        }
        if (frm.doc.custom_admission_status === "Letter Issued") {
            frm.add_custom_button(__("Offer Accepted"), function() {
                frm.events.show_confirmation(frm, "Offer Accepted");
            });
            frm.add_custom_button(__("Offer Rejected"), function() {
                frm.events.show_confirmation(frm, "Offer Rejected");
            });
        }
        if (frm.doc.custom_admission_status === "Offer Accepted") {
            frm.add_custom_button(__("Acceptance Paid"), function() {
                frm.events.show_confirmation(frm, "Acceptance Paid");
            });
        }

        frappe.realtime.on("create_applicant_progress", function(data) {
            if(data.progress) {
                frappe.hide_msgprint(true);
                frappe.show_progress(__("Creating Student Applicant"), data.progress[0], data.progress[1]);
            }
        });        
    },
    
    show_enroll_confirmation: function(frm) {
        frappe.confirm(
            __("Are you sure you want to create a Student Applicant from this Lead?"),
            function() {
                // Yes - proceed
                frm.events.enroll(frm);
            },
            function() {
                // No - cancel
            },
            __("Confirm Student Applicant Creation"),
            __("Create")
        );
    },
    
    enroll: function(frm) {
        frappe.model.open_mapped_doc({
            method: "edubliss.api.create_applicant",
            frm: frm
        });
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
                "lead": frm.doc.name,
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