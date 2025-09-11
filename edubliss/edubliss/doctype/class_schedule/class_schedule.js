// Copyright (c) 2025, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Class Schedule", {
	refresh(frm) {
        // apply query to restrict period_label in Subject Schedule
        frm.fields_dict["subject_schedule"].grid.get_field("period_label").get_query = function(doc, cdt, cdn) {
            if (!frm.doc.timetable_slot || !frm.doc.timetable_slot.length) {
                frappe.show_alert({
                    message: __("Please select a <b>Time Slots Template</b> before choosing Period Labels."),
                    indicator: "red"
                }, 5);

                return { filters: [["name", "=", ""]] };
            }

            // Allow only non-break period labels
            let allowed = frm.doc.timetable_slot
                .filter(r => !r.is_break)      // keep rows where is_break == 0
                .map(r => r.period_label)
                .filter(Boolean);

            return {
                filters: [["name", "in", allowed]]
            };
        };
	},

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
                        new_row.period_label = row.period_label;
                        new_row.start_time = row.start_time;
                        new_row.end_time = row.end_time;
                        new_row.label = row.label;
                        new_row.is_break = row.is_break ? 1 : 0;
                        new_row.duration = row.duration;
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
    },

    program(frm) {
        if (frm.doc.subject_schedule && frm.doc.subject_schedule.length) {
            frm.doc.subject_schedule.forEach((row) => {
                frappe.model.set_value(row.doctype, row.name, "course", "");
                frappe.model.set_value(row.doctype, row.name, "instructor", "");
            });
        }
        frm.refresh_field("subject_schedule");
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
    },

    course: function(frm, cdt, cdn) {
        let d = locals[cdt][cdn];

        if (!d.course) return;

        frappe.call({
            method: "edubliss.api.get_subjects_schedule_instructors",
            args: {
                course: d.course,
                academic_term: d.academic_term,
                student_group: d.student_group
            },
            callback: function(res) {
                if (res.message && res.message.length) {
                    if (res.message.length === 1) {
                        // Only one instructor → auto-set
                        frappe.model.set_value(cdt, cdn, "instructor", res.message[0]);
                    } else {
                        // Multiple instructors → let user pick
                        let dialog = new frappe.ui.Dialog({
                            title: __("Select Instructor"),
                            fields: [
                                {
                                    fieldtype: "Link",
                                    fieldname: "instructor",
                                    options: "Instructor",
                                    label: "Instructor",
                                    reqd: 1
                                }
                            ],
                            primary_action_label: __("Set"),
                            primary_action(values) {
                                frappe.model.set_value(cdt, cdn, "instructor", values.instructor);
                                dialog.hide();
                            }
                        });

                        dialog.set_values({ instructor: res.message[0] });
                        dialog.show();
                    }
                } else {
                    frappe.msgprint({
                        title: __("No Instructor Found"),
                        message: __("No instructor is mapped for this course, student group, and academic term."),
                        indicator: "red"
                    });
                    frappe.model.set_value(cdt, cdn, "instructor", "");
                }
            }
        });
    }
});

frappe.ui.form.on("Subject Schedule", {
    period_label(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    },
    from_time(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    },
    to_time(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    },
    week_days(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    },
    course(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    },
    instructor(frm, cdt, cdn) {
        validate_conflicts(frm, cdt, cdn);
    }
});

// helper function
function validate_conflicts(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);

    if (!row.week_days || !row.from_time || !row.to_time) {
        return;
    }

    // check against other rows in the same form
    frm.doc.subject_schedule.forEach(r => {
        if (r.name !== row.name && r.week_days === row.week_days) {
            let overlap = (row.from_time < r.to_time) && (row.to_time > r.from_time);

            if (overlap) {
                if (row.course && row.course === r.course) {
                    frappe.msgprint({
                        title: __("Conflict"),
                        indicator: "red",
                        message: __(`Course ${row.course} already scheduled on ${row.week_days} from ${r.from_time} to ${r.to_time}.`)
                    });
                }
                if (row.instructor && row.instructor === r.instructor) {
                    frappe.msgprint({
                        title: __("Conflict"),
                        indicator: "red",
                        message: __(`Instructor ${row.instructor} already scheduled on ${row.week_days} from ${r.from_time} to ${r.to_time}.`)
                    });
                }
            }
        }
    });

    // check against database
    // if (row.course || row.instructor) {
    //     frappe.call({
    //         method: "frappe.client.get_list",
    //         args: {
    //             doctype: "Subject Schedule",
    //             filters: {
    //                 week_days: row.week_days,
    //                 is_cancelled: 0,
    //                 name: ["!=", row.name],
    //             },
    //             fields: ["name", "from_time", "to_time", "course", "instructor", "parent"]
    //         },
    //         callback: function (res) {
    //             if (res.message) {
    //                 res.message.forEach(ss => {
    //                     let overlap = (row.from_time < ss.to_time) && (row.to_time > ss.from_time);
    //                     if (overlap) {
    //                         if (row.course && row.course === ss.course) {
    //                             frappe.msgprint({
    //                                 title: __("Conflict with DB"),
    //                                 indicator: "red",
    //                                 message: __(`Course ${row.course} already scheduled in ClassSchedule ${ss.parent} on ${row.week_days} from ${ss.from_time} to ${ss.to_time}.`)
    //                             });
    //                         }
    //                         if (row.instructor && row.instructor === ss.instructor) {
    //                             frappe.msgprint({
    //                                 title: __("Conflict with DB"),
    //                                 indicator: "red",
    //                                 message: __(`Instructor ${row.instructor} already scheduled in ClassSchedule ${ss.parent} on ${row.week_days} from ${ss.from_time} to ${ss.to_time}.`)
    //                             });
    //                         }
    //                     }
    //                 });
    //             }
    //         }
    //     });
    // }
}


