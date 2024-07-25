import frappe
from frappe import _

no_cache = 1

def get_context(context):
    docname = frappe.form_dict.docname

    # Ensure the user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)
    context.docname = frappe.form_dict.docname
    context.active_subroute = 'ledger'

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)
    

    return context
