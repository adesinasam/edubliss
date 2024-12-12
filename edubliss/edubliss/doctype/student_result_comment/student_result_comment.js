// Copyright (c) 2024, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Result Comment", {
	refresh: function(frm) {
		if (frm.doc.docstatus == 0) {
	    	// Add "Back" button
    		frm.page.set_secondary_action(`${frappe.utils.icon('arrow-left', 'sm')} ${__('Back to dashboard')}`, function() {
        		window.location.href = `/students/report_card/${frm.doc.student}`;
	   	 });
    	}
		if (frm.doc.docstatus == 1) {
	    	// Add "Back" button
    		frm.page.set_primary_action(`${frappe.utils.icon('arrow-left', 'sm')} ${__('Back to dashboard')}`, function() {
        		window.location.href = `/students/report_card/${frm.doc.student}`;
	   	 });
    	}
	},
});
