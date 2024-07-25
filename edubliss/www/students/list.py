import frappe
from frappe import _

no_cache = 1

def get_sales_invoices():
    return frappe.get_all('Sales Invoice', fields=['name', 'customer', 'posting_date', 'grand_total'])

def get_students():
    return frappe.get_all('Student', fields=['student_name', 'name', 'enabled', 'joining_date', 'student_email_id', 'image'])

def get_context(context):

    # Ensure the user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)
    context.sales_invoices = get_sales_invoices()
    context.students = get_students()

    # Count
    context.course_count = frappe.db.count('LMS Course')
    context.teacher_count = frappe.db.count('Instructor')
    context.student_count = frappe.db.count('Student')

    return context
