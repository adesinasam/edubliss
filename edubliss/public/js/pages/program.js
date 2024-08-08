frappe.ui.form.on('Program', {
    setup: function(frm) {
        frm.set_query("custom_school", function() {
            return {
                filters: [["Company","is_group", "=", 0]]}
        });
        frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    'custom_disabled': 0
                }
            };
        };
    }

})

// frappe.ui.form.on('Program', {
//     onload: function(frm) {
//         // Set a query for the child table's link field
//         frm.fields_dict['courses'].grid.get_field('course').get_query = function(doc, cdt, cdn) {
//             return {
//                 filters: {
//                     'custom_disabled': 0
//                 }
//             };
//         };
//     }
// })
