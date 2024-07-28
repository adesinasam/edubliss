import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def get_context(context):

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # nav
    context.active_route = "admission"

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
    context.admissions = frappe.call('edubliss.api.get_admissions')


    return context
