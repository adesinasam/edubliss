import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b, %Y"):
    if value:
        return value.strftime(format)
    return value

def get_structure_marks(student,assessment_plan):
    assessment_result = frappe.qb.DocType("Assessment Result")
    assessment_result_structure = frappe.qb.DocType("Assessment Result Structure")

    assessment_result_structure_query = (
        frappe.qb.from_(assessment_result)
        .inner_join(assessment_result_structure)
        .on(assessment_result.name == assessment_result_structure.parent)
        .select('*')
        .where(assessment_result.student == student)
        .where(assessment_result.assessment_plan == assessment_plan)
        .orderby(assessment_result_structure.idx)
        .run(as_dict=1)
    )
    return assessment_result_structure_query if assessment_result_structure_query else []

def get_criteria_marks(student,assessment_plan):
    assessment_result = frappe.qb.DocType("Assessment Result")
    assessment_result_criteria = frappe.qb.DocType("Assessment Result Detail")

    assessment_result_criteria_query = (
        frappe.qb.from_(assessment_result)
        .inner_join(assessment_result_criteria)
        .on(assessment_result.name == assessment_result_criteria.parent)
        .select('*')
        .where(assessment_result.student == student)
        .where(assessment_result.assessment_plan == assessment_plan)
        .orderby(assessment_result_criteria.idx)
        .run(as_dict=1)
    )
    return assessment_result_criteria_query if assessment_result_criteria_query else []

def get_total(student,assessment_plan):
    assessment_result = frappe.qb.DocType("Assessment Result")

    assessment_result_structure_query = (
        frappe.qb.from_(assessment_result)
        .select(assessment_result.total_score)
        .where(assessment_result.student == student)
        .where(assessment_result.assessment_plan == assessment_plan)
        .run(as_dict=1)
    )
    return assessment_result_structure_query[0]['total_score'] if assessment_result_structure_query else None

def get_comment(student,assessment_plan):
    assessment_result = frappe.qb.DocType("Assessment Result")

    assessment_result_structure_query = (
        frappe.qb.from_(assessment_result)
        .select(assessment_result.comment)
        .where(assessment_result.student == student)
        .where(assessment_result.assessment_plan == assessment_plan)
        .run(as_dict=1)
    )
    return assessment_result_structure_query[0]['comment'] if assessment_result_structure_query else None

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
    context.active_parent_route = "grade"
    context.section_url = f"admin/course/gradebook/{docname}"

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
    context.sections = frappe.call('edubliss.api.get_program_sections', company=company, academic_year=acadyear, course=docname)
    context['format_date'] = format_date

    try:
        context.courses = frappe.get_doc("Course", docname)
        course = context.courses
    except frappe.DoesNotExistError:
        frappe.throw(_("Course not found"), frappe.DoesNotExistError)

    section_name = frappe.form_dict.get('section_name')
    if section_name:
        context.selected_section = section_name
    else:
        context.selected_section = None

    # Initialize 'assessments' with a default value (None) to avoid UnboundLocalError
    assessments = None

    assessment_name = frappe.get_value("Assessment Plan", {
        "course": docname,
        "student_group": section_name,
        "academic_term": acadterm,
        "docstatus": 1
    })

    if assessment_name:
        context.assessment_name = assessment_name 
        context.assessments = frappe.get_doc("Assessment Plan", assessment_name)
        assessments = context.assessments  # Assign to 'assessments'
        context.students = frappe.call('edubliss.api.get_section_students', section=section_name)
        context['get_structure_marks'] = get_structure_marks
        context['get_criteria_marks'] = get_criteria_marks
        context['get_total'] = get_total
        context['get_comment'] = get_comment

    if assessments:  # Now this will only run if assessments is assigned
        context.criterias = assessments.get("assessment_criteria")
        context.structures = assessments.get("custom_assessment_structure")

    return context
