import frappe
from frappe import _

no_cache = 1

def get_courses(company):
    program_courses = frappe.qb.DocType("Program Course")
    courses = frappe.qb.DocType("Course")
    programs = frappe.qb.DocType("Program")

    program_courses_query = (
        frappe.qb.from_(program_courses)
        .inner_join(courses).on(program_courses.course == courses.course_name)
        .inner_join(programs).on(program_courses.parent == programs.name)
        .select(courses.name, courses.course_name, courses.custom_course_code, courses.custom_subject, 
        courses.custom_disabled, courses.custom_course_category, courses.department)
        .where(programs.custom_school == company)
        .where(courses.custom_disabled == 0)
        .orderby(courses.course_name)
        .run(as_dict=1)
    )
    return program_courses_query if program_courses_query else []


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
    context.active_route = "courses"
    context.active_subroute = "course_list"

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
    context.courses = get_courses(company)
    # context.courses = get_courses('Course', 
    #     filters={'custom_disabled': 0}, 
    #     fields=[
    #     'name', 'course_name', 'custom_course_code','custom_subject', 
    #     'custom_disabled', 'custom_course_category', 'department'], 
    #     order_by="course_name asc")

    # Count
    context.course_count = len(get_courses(company))
    context.lmscourse_count = frappe.db.count('LMS Course')

    return context
