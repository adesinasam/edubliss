import frappe
from frappe import _

no_cache = 1

def get_plan_instructors(assessment_plan):
    try:
        course_doc = frappe.get_doc('Assessment Plan', assessment_plan)
        return course_doc.custom_instructor
    except frappe.DoesNotExistError:
        return ""

def get_course_instructors(course,academic_year):
    instrutor = frappe.qb.DocType("Instructor")
    instrutor_course = frappe.qb.DocType("Instructor Log")

    instrutor_course_query = (
        frappe.qb.from_(instrutor)
        .inner_join(instrutor_course)
        .on(instrutor.name == instrutor_course.parent)
        .select(instrutor_course.parent)
        .where(instrutor_course.course == course)
        .where(instrutor_course.academic_year == academic_year)
        .run(as_dict=1)
    )
    return ", ".join(instructor['parent'] for instructor in instrutor_course_query) if instrutor_course_query else ""

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
    context.active_student_route = "gradebook"

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

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
        customer = context.students.customer
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

    try:
        results = frappe.get_all(
            "Assessment Result",
            fields=["name", "assessment_plan", "student", "course", "student_group",
             "total_score", "academic_term", "academic_year"],
            filters={
            "student": docname, 
            "academic_term": acadterm,
            "docstatus": ("!=", 2)
            },
            order_by="course",
        )
    except Exception as e:
        results = None  # or set a default value if required        

    if results:
        context.results = results    
        context['get_plan_instructors'] = get_plan_instructors
        context['get_course_instructors'] = get_course_instructors

    return context
