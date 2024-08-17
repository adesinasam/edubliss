frappe.ui.form.on('Lead', {
    refresh: function (frm) {
        if (frm.doc.status === "Quotation" && frm.doc.custom_admission_status === "Acceptance Paid") {
            frm.add_custom_button(__("Create Student Applicant"), function() {
                frm.events.enroll(frm)
            });
        }

        frappe.realtime.on("create_applicant_progress", function(data) {
            if(data.progress) {
                frappe.hide_msgprint(true);
                frappe.show_progress(__("Creating Student Applicant"), data.progress[0],data.progress[1]);
            }
        });        
    },
    enroll: function(frm) {
        frappe.model.open_mapped_doc({
            method: "edubliss.api.create_applicant",
            frm: frm
        })
    }
});

