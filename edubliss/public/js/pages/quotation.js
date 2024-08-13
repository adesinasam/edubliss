frappe.ui.form.on('Quotation', {
    party_name: function(frm) {
        if (frm.doc.quotation_to == "Customer"){
            frappe.db.get_value("Student", {"customer": frm.doc.party_name}, "name", function(value) {
                frm.doc.student = value.name;
                frm.set_value('student', value.name);
        refresh_field("student");
            });
	    }
    }
});

