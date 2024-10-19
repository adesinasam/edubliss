frappe.ui.form.on('Assessment Result Tool', {
	refresh: function(frm) {
	    // Add "Back" button
    	frm.page.set_secondary_action(`${frappe.utils.icon('arrow-left', 'sm')} ${__('Back')}`, function() {
        	window.location.href = `/admin/course/gradebook/${frm.doc.custom_course}?section_name=${frm.doc.student_group}`;
	    });
	},

	onload: function(frm) {
		frm.set_query('assessment_plan', function() {
			return {
				filters: {
					docstatus: 1
				}
			};
		});
	}
});
