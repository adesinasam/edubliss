
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
							row.week = d.week;
							row.assessment_type = d.assessment_type;
							row.assessment_criteria = d.assessment_criteria;
							row.topics = d.topics;
							row.weightage = d.weightage;
						});
					}
					refresh_field('custom_assessment_structure');

				}
			});
		}
	}
});
