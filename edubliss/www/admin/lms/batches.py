import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b %Y"):
    if value:
        return value.strftime(format)
    return value

def get_context(context):

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch the current user's details
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user

    # Fetch the roles of the current user
    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    # Split the company name into parts
    parts = current_user.full_name.split(" ")

    # Create the abbreviation by taking the first letter of each part
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # nav
    context.active_route = "lms"
    context.active_subroute = "lms_batch"

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.lmsbatches = frappe.get_all('LMS Batch', 
        filters={'custom_academic_year': acadyear}, 
        fields=[
        'name', 'title', 'seat_count', 'custom_academic_year', 'start_date', 'custom_program',
        'end_date', 'published', 'start_time', 'description', 'end_time'], 
        order_by="title asc")

    # Add this filter to Jinja
    context['format_date'] = format_date

    # Count
    context.lmscourse_count = frappe.db.count('LMS Course')
    context.lmsbatch_count = frappe.db.count('LMS Batch')

    return context
