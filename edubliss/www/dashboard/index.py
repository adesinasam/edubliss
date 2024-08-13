import frappe
from frappe import _

no_cache = 1

def get_context(context):
    # Redirect guest users to the portal
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch the current user's details
    context.current_user = frappe.get_doc("User", frappe.session.user)

    # Set the active route for navigation
    context.active_route = "dashboards"

    # Get session information
    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
    else:
        context.edublisession = _("Welcome")  # Placeholder message
        context.education_settings = frappe.call('edubliss.api.get_education_setting')
        context.request_url = frappe.request.url  # Placeholder message
        company = None

    # Fetch necessary data
    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.sales_invoices = frappe.call('edubliss.api.get_sales_invoices', company=company)
    context.students = frappe.call('edubliss.api.get_students', company=company)

    # Count various entities
    if company:
        context.student_count = frappe.db.count('Student', filters={'custom_school': company})
    else:
        context.student_count = frappe.db.count('Student')

    context.course_count = frappe.db.count('LMS Course')
    context.teacher_count = frappe.db.count('Instructor')

    return context
