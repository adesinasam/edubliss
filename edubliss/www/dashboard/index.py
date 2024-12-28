import frappe
from frappe import _

no_cache = 1

def get_teachers():
    instructors = frappe.qb.DocType("Instructor")
    employees = frappe.qb.DocType("Employee")

    instructors_query = (
        frappe.qb.from_(employees)
        .inner_join(instructors)
        .on(instructors.employee == employees.name)
        .select('*')
        .where(employees.user_id == frappe.session.user)
        .run(as_dict=1)
    )
    return instructors_query if instructors_query else []

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
    # Redirect guest users to the portal
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch the current user's details
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user

    # Fetch the roles of the current user
    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles
    
    if "Parent" in user_roles:
        guardian = frappe.get_list("Guardian", filters={"user": frappe.session.user}, limit_page_length=1)
        if guardian:
            context.parents = frappe.get_doc("Guardian", guardian[0].name)
            context.parents_name = guardian[0].name
        else:
            context.parents = ''
            context.parents_name = None

    if "Student" in user_roles:
        student = frappe.get_list("Student", filters={"student_email_id": frappe.session.user}, limit_page_length=1)
        if student:
            context.studentss = frappe.get_doc("Student", student[0].name)
            context.students_name = student[0].name
        else:
            context.studentss = ''
            context.students_name = None

    if "Instructor" in user_roles:
        teacher = get_teachers()
        if teacher:
            context.teachers = frappe.get_doc("Instructor", teacher[0].name)
            context.teachers_name = teacher[0].name
        else:
            context.teachers = ''
            context.teacher_name = None

    # Split the company name into parts
    parts = current_user.full_name.split(" ")

    # Create the abbreviation by taking the first letter of each part
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # Set the active route for navigation
    context.active_route = "dashboards"

    # Get session information
    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Placeholder message
        context.education_settings = frappe.call('edubliss.api.get_education_setting')
        context.request_url = frappe.request.url  # Placeholder message
        company = None
        acadyear = None
        acadterm = None

    # Fetch necessary data
    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.sales_invoices = frappe.call('edubliss.api.get_sales_invoices', company=company)
    context.students = frappe.call('edubliss.api.get_students', company=company)

    # Count various entities
    if company:
        context.student_count = frappe.db.count('Student', filters={'custom_school': company})
        context.teacher_count = len(frappe.call('edubliss.api.get_teachers', company=company))
        context.program_count = frappe.db.count('Program', filters={'custom_school': company})
        context.course_count = len(get_courses(company))
        context.applicants_count = frappe.db.count('Student Applicant', 
            filters={'custom_school': company,
            'academic_year': acadyear,
            'academic_term': acadterm}
            )
        context.assessments_count = len(frappe.call('edubliss.api.get_assessments', company=company,academic_term=acadterm))
    else:
        context.student_count = frappe.db.count('Student')
        context.teacher_count = 0
        context.program_count = 0
        context.course_count = frappe.db.count('Course')
        context.applicants_count = 0
        context.assessments_count = 0

    context.lmscourse_count = frappe.db.count('LMS Course')

    return context
