frappe.ui.form.on('Program Enrollment Tool', {
  enroll_students: function (frm) {
    if (frm.doc.is_transfer) {
      frappe.call({
        method: 'edubliss.api.update_transfer_status',
        args: {  // Missing 'args' parameter
          enrollment_tool_doc: frm.doc
        },
        callback: function (r) {
          frm.set_value('students', [])
          frappe.hide_msgprint(true)
        },
      })
    }
  },
})
