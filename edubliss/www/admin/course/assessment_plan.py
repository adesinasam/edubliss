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
    context.active_parent_route = "assessment_plan"
    context.section_url = f"admin/course/assessment_plan/{docname}"
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
        acadterm = None  # Set acadterm to None to avoid potential errors if no session exists

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.programs = frappe.call('edubliss.api.get_programs', company=company)
    context.sections = frappe.call('edubliss.api.get_program_sections', company=company, academic_term=acadterm, course=docname)

    try:
        context.courses = frappe.get_doc("Course", docname)
        course = context.courses
    except frappe.DoesNotExistError:
        frappe.throw(_("Course not found"), frappe.DoesNotExistError)

    section_name = frappe.form_dict.get('section_name')
    if section_name:
        context.selected_section = section_name
        context.section_name = frappe.get_doc("Student Group", section_name)
        context.students = frappe.call('edubliss.api.get_section_students', section=section_name)
    else:
        context.selected_section = None
        context.section_name = None
        context.students = []

    # Initialize 'assessments' with a default value (None) to avoid UnboundLocalError
    assessments = None

    assessment_name = frappe.get_value("Assessment Plan", {
        "course": docname,
        "student_group": section_name,
        "academic_term": acadterm,
        "docstatus": 1
    })

    if assessment_name:
        context.assessments = frappe.get_doc("Assessment Plan", assessment_name)
        assessments = context.assessments  # Assign to 'assessments'

    if assessments:  # Now this will only run if assessments is assigned
        context.criterias = assessments.get("assessment_criteria")
        context.structures = assessments.get("custom_assessment_structure")

    return context
