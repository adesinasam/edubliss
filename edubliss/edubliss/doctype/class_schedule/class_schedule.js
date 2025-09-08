// Copyright (c) 2025, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Class Schedule", {
	// refresh(frm) {

	// },

    onload(frm) {
        // apply query on the "course" field inside the child table "subjects"
        frm.fields_dict["subject_schedule"].grid.get_field("course").get_query = function (doc, cdt, cdn) {
            return {
                query: "education.education.doctype.program_enrollment.program_enrollment.get_program_courses",
                filters: {
                    program: frm.doc.program,
                },
            };
        };
    },

    time_slots_template: function(frm) {
        // Fetch and set timetable_slot when time_slots_template changes
        if (!frm.doc.time_slots_template) {
            frm.set_value("timetable_slot", []);
            return;
        }
        
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Time Slots Template",
                name: frm.doc.time_slots_template,
                fieldname: ["timetable_slot"]
            },
            callback: function(response) {
                if (response.message && response.message.timetable_slot) {
                    frm.set_value("timetable_slot", []);
                    
                    response.message.timetable_slot.forEach(function(row) {
                        var new_row = frm.add_child("timetable_slot");
                        new_row.label = row.label;
                        new_row.start_time = row.start_time;
                        new_row.end_time = row.end_time;
                        new_row.duration = row.duration;
                        new_row.is_break = row.is_break;
                    });
                    
                    frm.refresh_field("timetable_slot");
                }
            }
        });
    },

    student_group(frm) {
        // Update existing rows when parent field changes
        if (frm.doc.subject_schedule && frm.doc.subject_schedule.length) {
            frm.doc.subject_schedule.forEach((item, i) => {
                frappe.model.set_value(item.doctype, item.name, "student_group", frm.doc.student_group);
                frappe.model.set_value(item.doctype, item.name, "program", frm.doc.program);
                frappe.model.set_value(item.doctype, item.name, "academic_year", frm.doc.academic_year);
                frappe.model.set_value(item.doctype, item.name, "academic_term", frm.doc.academic_term);
            });
        }
    }

});

// Trigger on child table row add
frappe.ui.form.on("Subject Schedule", {
    subject_schedule_add(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (frm.doc.student_group) {
            frappe.model.set_value(cdt, cdn, "student_group", frm.doc.student_group);
            frappe.model.set_value(cdt, cdn, "program", frm.doc.program);
            frappe.model.set_value(cdt, cdn, "academic_year", frm.doc.academic_year);
            frappe.model.set_value(cdt, cdn, "academic_term", frm.doc.academic_term);
        }
    }
});
