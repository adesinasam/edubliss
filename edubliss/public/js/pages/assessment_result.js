frappe.ui.form.on('Assessment Result', {
	refresh: function(frm) {
		frm.get_field('custom_structure_detail').grid.cannot_add_rows = true;
	},

	assessment_plan: function(frm) {
		if (frm.doc.assessment_plan) {
			frappe.call({
				method: 'edubliss.api.get_assessment_structure_details',
				args: {
					assessment_plan: frm.doc.assessment_plan
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.clear_table(frm.doc, 'custom_structure_detail');
						$.each(r.message, function(i, d) {
							var row = frm.add_child('custom_structure_detail');
							row.assessment_type = d.assessment_type;
							row.assessment_criteria = d.assessment_criteria;
							row.topics = d.topics;
							row.maximum_score = d.max_score;
							row.weightage = d.weightage;
						});
						frm.refresh_field('custom_structure_detail');
					}
				}
			});
		}
	}
});

frappe.ui.form.on('Assessment Result Structure', {
    score: function(frm, cdt, cdn) {
        var d  = locals[cdt][cdn];

        // Calculate percentage and weightage
        let percentages = ((d.score / d.maximum_score) * 100);
        let weightages = ((d.score / d.maximum_score) * d.weightage);

        // Call to get grade based on percentage
        frappe.call({
            method: 'education.education.api.get_grade',
            args: {
                grading_scale: frm.doc.grading_scale,
                percentage: percentages
            },
            callback: function(r) {
                if (r.message) {
                    // Update Assessment Result Structure with grade and weightage score
                    frappe.model.set_value(cdt, cdn, 'grade', r.message);
                    frappe.model.set_value(cdt, cdn, 'weightage_score', weightages);

                    // Now sum 'weightage_score' based on 'assessment_criteria' in Assessment Result Structure
                    let total_weightage_score = 0;
                    frm.doc.custom_structure_detail.forEach(row => {
                        if (row.assessment_criteria === d.assessment_criteria) {
                            total_weightage_score += row.weightage_score || 0;
                        }
                    });

                    // Find corresponding row in Assessment Result Detail and update 'maximum_score'
                    let detail_row = frm.doc.details.find(detail => detail.assessment_criteria === d.assessment_criteria);

                    if (detail_row) {
                        frappe.model.set_value(detail_row.doctype, detail_row.name, 'score', total_weightage_score);
                    }
                }
            }
        });
    }
});

