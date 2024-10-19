
frappe.ui.form.on('Assessment Plan', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
	    	// Add "Back" button
    		frm.page.set_primary_action(`${frappe.utils.icon('arrow-left', 'sm')} ${__('Back to dashboard')}`, function() {
        		window.location.href = `/admin/course/assessment_plan/${frm.doc.course}?section_name=${frm.doc.student_group}`;
	   	 });
    	}
	},

	course: function(frm) {
		if (frm.doc.course && frm.doc.maximum_assessment_score) {
			frappe.call({
				method: 'edubliss.api.get_assessment_structure',
				args: {
					course: frm.doc.course
				},
				callback: function(r) {
					if (r.message) {
						frm.doc.custom_assessment_structure = [];
						$.each(r.message, function(i, d) {
							var row = frappe.model.add_child(frm.doc, 'Assessment Plan Structure', 'custom_assessment_structure');
							row.week = d.week;
							row.assessment_type = d.assessment_type;
							row.assessment_criteria = d.assessment_criteria;
							row.topics = d.topics;
							row.weightage = d.weightage;
							row.description = d.description;
						});
					}
					refresh_field('custom_assessment_structure');

				}
			});
		}
	}
});
