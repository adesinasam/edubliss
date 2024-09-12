frappe.ui.form.on('Course Scheduling Tool', {
	onload: (frm) => {
		frm.set_query('course', function() {
			return {
				query: 'education.education.doctype.program_enrollment.program_enrollment.get_program_courses',
				filters: {
					'program': frm.doc.program
				}
			};
		});

	}
});
