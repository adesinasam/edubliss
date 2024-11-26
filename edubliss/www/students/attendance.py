import frappe
from frappe import _

no_cache = 1

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
    context.active_student_route = "attendance"

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
                academic_term=acadterm
                )
        except Exception as e:
            sections = None  # or set a default value if required        

        if sections:
            context.sections = frappe.get_doc("Student Group", sections)
            context.sections_name = sections

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

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
        context.student_name = context.students.name
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

    # Fetch courses based on the selected section, if any
    course_name = frappe.form_dict.get('course_name')
    if course_name:
        context.selected_course = course_name
    else:
        context.selected_course = None


    return context
