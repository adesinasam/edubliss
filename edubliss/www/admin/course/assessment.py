import frappe
from frappe import _

no_cache = 1

def get_context(context):

    docname = frappe.form_dict.docname

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
    context.active_route = "courses"
    context.active_subroute = "course_list"
    context.active_parent_route = "assessment"
    context.active_teacher_route = "course"

    context.docname = frappe.form_dict.docname

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    academic_term = frappe.get_doc("Academic Term", acadterm)
    terms = academic_term.term_name

    try:
        context.courses = frappe.get_doc("Course", docname)
        course = context.courses
    except frappe.DoesNotExistError:
        frappe.throw(_("Course not found"), frappe.DoesNotExistError)

    # Try to fetch the Student document and handle errors if it doesn't exist
    if course:
        context.criterias = course.get("assessment_criteria")
        context.structures = course.get("assessment_structure")
        context.outlines = course.get("custom_outline")
    

    return context
