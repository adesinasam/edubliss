import frappe
from frappe import _

no_cache = 1

def get_sales_invoices():
    return frappe.get_all('Sales Invoice', fields=['name', 'title', 'status', 'posting_date', 'grand_total', 'outstanding_amount', 'customer'])

def get_students():
    return frappe.get_all('Student', fields=['student_name', 'name', 'enabled', 'joining_date', 'image'])

def get_context(context):
    active_subroute = "profile"

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # Sales Invoices
    context.sales_invoices = get_sales_invoices()

    # Sales Invoices
    context.sales_invoices = get_sales_invoices()

    # Student
    context.students = frappe.db.sql("""
        SELECT student_name, name, enabled, joining_date, student_email_id, image 
        FROM `tabStudent`;
        """, as_dict=True)
    
    # Count
    context.course_count = frappe.db.count('LMS Course')
    context.teacher_count = frappe.db.count('Instructor')
    context.student_count = frappe.db.count('Student')

    # nav
    context.active_subroute = active_subroute

    # Add other Doctypes as needed
    # context.other_doctype_count = frappe.db.count('Other Doctype')
    # context.teacher_count = frappe.db.count('Instructor')
    # context.teacher_count = frappe.db.count('Instructor')
    # context.teacher_count = frappe.db.count('Instructor')

    return context

