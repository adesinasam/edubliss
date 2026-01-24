import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_day(value, format="%d"):
    if value:
        return value.strftime(format)
    return value

def format_month(value, format="%b, %Y"):
    if value:
        return value.strftime(format)
    return value

def format_year(value, format="%Y"):
    if value:
        return value.strftime(format)
    return value

def truncate_words(text, word_limit=100):
    words = text.split()
    if len(words) > word_limit:
        return " ".join(words[:word_limit]) + "..."
    return text

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
    context.active_route = "notices"
    context.active_subroute = "notices"

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term
    context['format_day'] = format_day
    context['format_month'] = format_month
    context['format_year'] = format_year
    context['truncate_words'] = truncate_words    

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.notices = frappe.get_all(
        'Newsletter', 
        filters={'published': 1}, 
        fields=['*'], 
        order_by='modified desc'
        )

    # Count
    context.program_count = frappe.db.count('Program', filters={'custom_school': company})
    context.lmsbatch_count = frappe.db.count('LMS Batch')

    return context
