import frappe
from frappe import _

no_cache = 1

def get_context(context):
    docname = frappe.form_dict.docname

    # Ensure the user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)
    context.docname = docname
    context.active_subroute = 'billing'

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)
    
    # Ensure the customer field exists on the student document
    # if not hasattr(context.students, 'customer'):
    #     frappe.throw(_("The student document does not have a customer field"), frappe.ValidationError)

    # Fetch sales invoices
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={"customer": context.students.customer},
        fields=["name", "title", "status", "posting_date", "grand_total", "outstanding_amount", "customer"],
        order_by="posting_date desc"
    )
    context.sales_invoices = sales_invoices

    return context
