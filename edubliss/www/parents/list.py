import frappe
from frappe import _

no_cache = 1

def get_parent_students(parent):
    guardian = frappe.qb.DocType("Guardian")
    guardian_student = frappe.qb.DocType("Guardian Student")

    guardian_student_query = (
        frappe.qb.from_(guardian)
        .inner_join(guardian_student)
        .on(guardian.name == guardian_student.parent)
        .select(guardian_student.student)
        .where(guardian.name == parent)
        .run(as_dict=1)
    )
    return len(guardian_student_query)

def get_context(context):

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # nav
    context.active_route = "parents"
    context.active_subroute = "parent_list"

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
    context.sales_invoices = frappe.call('edubliss.api.get_sales_invoices', company=company)
    context.students = frappe.call('edubliss.api.get_students', company=company)
    context.parents = frappe.call('edubliss.api.get_parents')
    context['get_parent_students'] = get_parent_students

    # Count
    context.parent_count = frappe.db.count('Guardian')


    return context
