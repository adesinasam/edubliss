import frappe
from frappe import _

no_cache = 1

def get_section_teachers(section):
    student_group = frappe.qb.DocType("Student Group")
    student_group_instructors = frappe.qb.DocType("Student Group Instructor")

    student_group_query = (
        frappe.qb.from_(student_group)
        .inner_join(student_group_instructors)
        .on(student_group.name == student_group_instructors.parent)
        .select(student_group_instructors.instructor)
        .where(student_group.name == section)
        .run(as_dict=1)
    )
    return ", ".join(instructor['instructor'] for instructor in student_group_query) if student_group_query else ""

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
    context.active_route = "timetable"
    context.active_subroute = "timetable"
    context.section_url = "admin/timetable"

    # Fetch edubliss session details
    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Placeholder message
        company = None
        acadyear = None

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    # Fetch necessary data
    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.programs = frappe.call('edubliss.api.get_programs', company=company)
    context.sections = frappe.call('edubliss.api.get_sections', company=company, academic_term=acadterm)
    context['get_section_teachers'] = get_section_teachers

    # Fetch courses based on the selected section, if any
    section_name = frappe.form_dict.get('section_name')
    if section_name:
        context.selected_section = section_name
        context.students = frappe.call('edubliss.api.get_section_students', section=section_name)
    else:
        context.selected_section = None
        context.students = []


    return context
