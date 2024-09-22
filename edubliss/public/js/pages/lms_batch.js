frappe.ui.form.on("LMS Batch", {
    onload: function(frm) {
        frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
            let child = locals[cdt][cdn];

            // Initialize an array to store selected course names
            let selected_courses = [];

            // Loop through the child table and collect the course values
            if (frm.doc.courses) {
                frm.doc.courses.forEach(function(row) {
                    if (row.course) {
                        selected_courses.push(row.course);
                    }
                });
            }

            return {
                filters: [
                    ['custom_program', '=', frm.doc.custom_program],   // Filter by selected program
                    ['name', 'not in', selected_courses] // Exclude already picked courses
                ]
            };
        };
    },
    setup: function(frm) {
        frm.set_query("custom_student_group", function() {
            return {
                filters: {
                    'academic_year': frm.doc.custom_academic_year || "", // Safeguard in case fields are empty
                    'program': frm.doc.custom_program || ""
                }
            }
        });
    },
    refresh: function(frm) {
        frm.fields_dict['students'].grid.get_field('student').get_query = function(doc, cdt, cdn) {
            let student_group = frm.doc.custom_student_group;

            // Ensure student_group is selected
            if (!student_group || student_group.length === 0) {
                frappe.msgprint(__('Please select at least one Student Group.'));
                return false;
            }

            // Extract student group names (or IDs) from the selected rows
            let student_group_names = student_group.map(row => row.student_group);

            // Get a list of already selected students from the "students" child table
            let selected_users = (frm.doc.students || []).map(row => row.student);

            // Query to filter users based on students in the selected Student Groups
            return {
                query: "edubliss.edubliss.lms_batch.get_users_for_student_group",
                filters: {
                    "student_group": student_group_names,  // Pass the selected student groups (multiselect) to the query
                    "excluded_users": selected_users  // Exclude already selected students
                }
            };
        };
    }

    // refresh: function(frm) {
    //     frm.fields_dict['students'].grid.get_field('student').get_query = function(doc, cdt, cdn) {
    //         let student_group = frm.doc.custom_student_group;

    //         // Ensure student_group is selected
    //         if (!student_group) {
    //             frappe.msgprint(__('Please select a Student Group first.'));
    //             return false;
    //         }

    //         // Query to filter users based on students in the selected Student Group
    //         return {
    //             query: "edubliss.edubliss.lms_batch.get_users_for_student_group",
    //             filters: {
    //                 "student_group": student_group  // Filter students based on selected Student Group
    //             }
    //         };
    //     };
    // }    
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
