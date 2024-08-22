import frappe
from frappe import _

no_cache = 1

def get_program_course_code(course):
    try:
        course_doc = frappe.get_doc('Course', course)
        return course_doc.custom_course_code
    except Exception as e:
        return ''       

def get_program_course_category(course):
    try:
        course_doc = frappe.get_doc('Course', course)
        return course_doc.custom_course_category
    except Exception as e:
        return ''       

def get_program_course_subject(course):
    try:
        course_doc = frappe.get_doc('Course', course)
        return course_doc.custom_subject
    except Exception as e:
        return ''       

def get_context(context):
    # Check if the user is logged in
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

    # Set active route for navigation
    context.active_route = "program"
    context.active_subroute = "programs"

    # Fetch edubliss session details
    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
    else:
        context.edublisession = _("Welcome")  # Placeholder message
        company = None

    # Fetch necessary data
    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.programs = frappe.call('edubliss.api.get_programs', company=company)

    # Fetch courses based on the selected program, if any
    program_name = frappe.form_dict.get('program_name')
    if program_name:
        context.selected_program = program_name
        context.courses = frappe.call('edubliss.api.get_program_courses', program=program_name)
        context['get_program_course_code'] = get_program_course_code
        context['get_program_course_subject'] = get_program_course_subject
        context['get_program_course_category'] = get_program_course_category
    else:
        context.selected_program = None
        context.courses = []


    return context
