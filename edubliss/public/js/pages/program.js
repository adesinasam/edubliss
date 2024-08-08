frappe.ui.form.on('Program', {
    setup: function(frm) {
        frm.set_query("custom_school", function() {
            return {
                filters: [["Company","is_group", "=", 0]]}
        });
    }

})
