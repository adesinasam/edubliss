frappe.ui.form.on('Sales Invoice', {
    refresh(frm) {
        // your code here
        cur_frm.add_fetch('program',  'custom_school',  'company');        // your code here
    },
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

