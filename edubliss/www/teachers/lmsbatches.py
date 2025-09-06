import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b %Y"):
    if value:
        return value.strftime(format)
    return value

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

def get_batches(acadyear):
    batches = frappe.qb.DocType("LMS Batch")
    instructors = frappe.qb.DocType("Course Instructor")

    batches_query = (
        frappe.qb.from_(batches)
        .inner_join(instructors)
        .on(instructors.parent == batches.name)
        .select('name', 'title', 'seat_count', 'custom_academic_year', 'start_date', 'custom_program',
        'end_date', 'published', 'start_time', 'description', 'end_time')
        .where(instructors.instructor == frappe.session.user)
        .where(batches.custom_academic_year == acadyear)
        .orderby(batches.title)
        .run(as_dict=1)
    )
    return batches_query if batches_query else []

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
    context.active_subroute = "lms_batch"

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
    context.lmsbatches = get_batches(acadyear=acadyear)

    # Add this filter to Jinja
    context['format_date'] = format_date

    # Count
    context.lmsbatch_count = len(get_batches(acadyear=acadyear))

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
