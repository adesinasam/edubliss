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
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Placeholder message
        context.education_settings = frappe.call('edubliss.api.get_education_setting')
        context.request_url = frappe.request.url  # Placeholder message
        company = None
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
    else:
        context.student_count = frappe.db.count('Student')

    context.course_count = frappe.db.count('Course')
    context.teacher_count = frappe.db.count('Instructor')

    return context
