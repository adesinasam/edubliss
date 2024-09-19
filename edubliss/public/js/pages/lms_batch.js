frappe.ui.form.on("LMS Batch", {
    onload: function(frm) {
        frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    'custom_program': frm.doc.custom_program  // Filters based on program field in the parent doctype
                }
            };
        };
    },
    setup: function(frm) {
        frm.set_query("custom_student_group", function() {
            return {
                filters: {
                    'academic_year': frm.doc.custom_academic_year  // Filters based on program field in the parent doctype
                }
            }
        });
        frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];
            return {
                filters: {
                    'custom_program': frm.doc.custom_program  // Filters based on program field in the parent doctype
                }
            };
        };
        frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    'published': 0
                }
            };
        };
    }
	// custom_program: function(frm) {
	// 	frm.events.get_courses(frm);
	// },
	// get_courses: function(frm) {
	// 	frm.program_courses = [];
	// 	frm.set_value('courses',[]);
	// 	frappe.call({
	// 		method: 'edubliss.edubliss.lms_batch.get_courses',
	// 		args: {
	// 			'program': frm.doc.custom_program
	// 		},
	// 		callback: function(r) {
	// 			if (r.message) {
	// 				frm.program_courses = r.message
	// 				frm.set_value('courses', r.message);
	// 			}
	// 		}
	// 	})
	// }

});
