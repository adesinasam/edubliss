import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b, %Y"):
    if value:
        return value.strftime(format)
    return value

def get_structure_date(assessment_plan,assessment_type, format="%d %b, %Y"):
    plan_structure = frappe.qb.DocType("Assessment Plan Structure")

    assessment_plan_structure_query = (
        frappe.qb.from_(plan_structure)
        .select(plan_structure.schedule_date)
        .where(plan_structure.parent == assessment_plan)
        .where(plan_structure.assessment_type == assessment_type)
        .run(as_dict=1)
    )
    value=assessment_plan_structure_query[0]['schedule_date'] if assessment_plan_structure_query else None
    if value:
        return value.strftime(format)
    return value

def get_structure_due(assessment_plan,assessment_type, format="%d %b, %Y"):
    plan_structure = frappe.qb.DocType("Assessment Plan Structure")

    assessment_plan_structure_query = (
        frappe.qb.from_(plan_structure)
        .select(plan_structure.due_date)
        .where(plan_structure.parent == assessment_plan)
        .where(plan_structure.assessment_type == assessment_type)
        .run(as_dict=1)
    )
    value=assessment_plan_structure_query[0]['due_date'] if assessment_plan_structure_query else None
    if value:
        return value.strftime(format)
    return value

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
    context.active_route = "students"
    context.active_subroute = "student_list"
    context.active_student_route = "gradebook"

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

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    # Try to fetch the Student Program Enrollment document and handle errors if it doesn't exist
    try:
        program = frappe.call(
            'edubliss.api.get_student_program',
            student=docname, 
            academic_year=acadyear, 
            academic_term=acadterm
        )
    except Exception as e:
        program = ''  # or set a default value if required        

    if program:
        context.program = program
        program_enrollment = context.program.name   
        program_name = context.program.program
        context.program_courses = frappe.call('edubliss.api.get_program_courses', program=program_name)

        # Try to fetch the Student Group document and handle errors if it doesn't exist
        try:
            sections = frappe.call(
                'edubliss.api.get_student_groups', 
                student=docname, 
                program=program_name, 
                academic_year=acadyear
                )
        except Exception as e:
            sections = None  # or set a default value if required        

        if sections:
            context.sections = sections    

        # Try to fetch the Student Courses document and handle errors if it doesn't exist
        try:
            courses = frappe.call(
                'edubliss.api.get_student_courses',
                student=docname, 
                program_enrollment=program_enrollment
                )
        except Exception as e:
            courses = None  # or set a default value if required        

        if courses:
            context.courses = courses    

    else:
        context.program = _("Welcome")  # or set a default value if required

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context['format_date'] = format_date

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
        customer = context.students.customer
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

    assessment_result = frappe.form_dict.get('name')

    if assessment_result:
        context.assessment_result = assessment_result
        results = frappe.get_doc("Assessment Result", assessment_result)
        context.results = results
        context.criterias = results.get("details")
        context.structures = results.get("custom_structure_detail")

        context['get_structure_date'] = get_structure_date
        context['get_structure_due'] = get_structure_due

    return context