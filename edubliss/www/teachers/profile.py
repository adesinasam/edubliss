import frappe
from frappe import _

no_cache = 1

def get_context(context):

    docname = frappe.form_dict.docname

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)

    # nav
    context.active_route = "teachers"
    context.active_subroute = "teacher_list"
    context.active_teacher_route = "profile"

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

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    # Try to fetch the Student Program document and handle errors if it doesn't exist
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
    else:
        context.program = _("Welcome")  # or set a default value if required

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    context.teachers = frappe.call('edubliss.api.get_teachers')

    # Try to fetch the Student document and handle errors if it doesn't exist
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