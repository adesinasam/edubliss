import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b %Y"):
    if value:
        return value.strftime(format)
    return value

def get_program_course_status(course):
    try:
        course_doc = frappe.get_doc('LMS Course', course)
        return course_doc.status
    except frappe.DoesNotExistError:
        return ""

def get_program_course_published(course):
    try:
        course_doc = frappe.get_doc('LMS Course', course)
        return course_doc.published
    except frappe.DoesNotExistError:
        return ""

def get_program_course_image(course):
    try:
        course_doc = frappe.get_doc('LMS Course', course)
        return course_doc.image
    except frappe.DoesNotExistError:
        return ""

def get_program_course_intro(course):
    try:
        course_doc = frappe.get_doc('LMS Course', course)
        return course_doc.short_introduction
    except frappe.DoesNotExistError:
        return ""

def get_context(context):

    docnames = frappe.form_dict.docname

    if docnames:
        docname = docnames
    else:
        student = frappe.get_list("Student", filters={"student_email_id": frappe.session.user}, limit_page_length=1)
        if student:
            docname = student[0].name
        else:
            docname = None

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
    context.active_student_route = "lms"

    context.docname = docname

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

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        students = frappe.get_doc("Student", docname)
        context.students = students
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

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
            lmsbatch = frappe.call(
                'edubliss.api.get_student_lmsbatch',
                student=students.user, 
                program=program.program, 
                student_group=sections 
                )

            lmsbatches = frappe.get_doc('LMS Batch', lmsbatch)
            lmscourses = frappe.get_all(
                'Batch Course', 
                filters={"parent": lmsbatch}, 
                fields=["course", "title", "evaluator"]
                )
        except Exception as e:
            lmsbatches = None  # or set a default value if required 
            lmscourses = None       

        if lmsbatches:
            context.lmsbatches = lmsbatches    
            context.lmscourses = lmscourses    


        # Add this filter to Jinja
        context['format_date'] = format_date

        # Add custom filters to the context
        context['get_program_course_status'] = get_program_course_status
        context['get_program_course_published'] = get_program_course_published
        context['get_program_course_image'] = get_program_course_image
        context['get_program_course_intro'] = get_program_course_intro

    else:
        context.program = _("Welcome")  # or set a default value if required

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')



    return context
