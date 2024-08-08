import frappe
from frappe import _

no_cache = 1

def get_company_students(company):
    try:
        student_doc = frappe.db.count('Student', filters={'custom_school': company,})
        return student_doc
    except frappe.DoesNotExistError:
        return ""

def get_context(context):

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # nav
    context.active_route = "school"
    context.active_subroute = "schools"

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    context['get_company_students'] = get_company_students
    context.company_count = frappe.db.count('Company', filters={'is_group': 0})

    return context
