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

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # nav
    context.active_route = "program"
    context.active_subroute = "section_list"

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.teachers = frappe.call('edubliss.api.get_teachers', company=company)
    context.sections = frappe.call('edubliss.api.get_sections', company=company)
    context['get_section_teachers'] = get_section_teachers

    # Count
    if company:
        context.student_count = frappe.db.count('Student', filters={'custom_school': company})
    else:
        context.student_count = frappe.db.count('Student')

    context.course_count = frappe.db.count('LMS Course')
    context.section_count = len(frappe.call('edubliss.api.get_sections', company=company))

    return context
