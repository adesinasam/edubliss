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

def get_courses():
    courses = frappe.qb.DocType("LMS Course")
    instructors = frappe.qb.DocType("Course Instructor")

    courses_query = (
        frappe.qb.from_(courses)
        .inner_join(instructors)
        .on(instructors.parent == courses.name)
        .select('name', 'title', 'image', 'published_on', 'upcoming', 'custom_course',
        'status', 'published', 'featured', 'short_introduction', 'disable_self_learning')
        .where(instructors.instructor == frappe.session.user)
        .orderby(courses.title)
        .run(as_dict=1)
    )
    return courses_query if courses_query else []

def get_context(context):

    docnames = frappe.form_dict.docname

    if docnames:
        docname = docnames
    else:
        teacher = get_teachers()
        if teacher:
            docname = teacher[0].name
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
    context.active_route = "lms"
    context.active_subroute = "lms_course"

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

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.lmscourses = get_courses()

    # Count
    context.lmscourse_count = len(get_courses())

    try:
        context.teachers = frappe.get_doc("Instructor", docname)
        staff = context.teachers
    except frappe.DoesNotExistError:
        frappe.throw(_("Teacher not found"), frappe.DoesNotExistError)

    if staff:
        try:
            context.employees = frappe.get_doc("Employee", staff.employee)
        except frappe.DoesNotExistError:
            frappe.throw(_("Employee Record not found"), frappe.DoesNotExistError)


    return context
