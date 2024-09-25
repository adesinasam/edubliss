
frappe.ui.form.on('Assessment Plan', {
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
							row.schedule_date = d.schedule_date;
							row.due_date = d.due_date;
							row.week = d.week;
							row.assessment_type = d.assessment_type;
							row.assessment_criteria = d.assessment_criteria;
							row.topics = d.topics;
							row.max_score = d.max_score;
							row.weightage = d.weightage;
							// row.maximum_score = d.weightage / 100 * frm.doc.maximum_assessment_score;
						});
					}
					refresh_field('custom_assessment_structure');

				}
			});
		}
	}
});
