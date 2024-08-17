import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils.dateutils import get_dates_from_timegrain


@frappe.whitelist()
def process_selected_values(company, academic_year, academic_term):
    company_data = frappe.get_doc('Company', company)
    academic_year_data = frappe.get_doc('Academic Year', academic_year)
    academic_term_data = frappe.get_doc('Academic Term', academic_term)
    
    return {
        'company': company_data,
        'academic_year': academic_year_data,
        'academic_term': academic_term_data
    }

@frappe.whitelist()
def get_student_program(student=None, academic_year=None, academic_term=None):
    filters = {
        'student': student,
        'academic_year': academic_year,
        'academic_term': academic_term,
        'docstatus': ['<', 2]
    }
    return frappe.get_doc('Program Enrollment', filters)

@frappe.whitelist()
def get_student_groups(student, program=None):
    student_group = frappe.qb.DocType("Student Group")
    student_group_students = frappe.qb.DocType("Student Group Student")

    student_group_query = (
        frappe.qb.from_(student_group)
        .inner_join(student_group_students)
        .on(student_group.name == student_group_students.parent)
        .select(student_group_students.parent)
        .where(student_group_students.student == student)
        .where(student_group.program == program)
        .where(student_group.disabled == 0)
        .run(as_dict=1)
    )

    return student_group_query[0]['parent'] if student_group_query else None

@frappe.whitelist()
def get_student_courses(student=None, program_enrollment=None):
    filters = {}

    if student:
        filters['student'] = student
    if program_enrollment:
        filters['program_enrollment'] = program_enrollment

    return frappe.get_all(
        'Course Enrollment', 
        filters=filters, 
        fields=[
        'name', 'program_enrollment', 'program', 'enrollment_date', 
        'student_name', 'student', 'course'
        ], 
        order_by="course asc"
        )

@frappe.whitelist(allow_guest=True)
def get_program_courses(program):
    return frappe.get_all(
        "Program Course",
        filters={"parent": program},
        fields=["course", "course_name", "required"]
    )

@frappe.whitelist(allow_guest=True)
def get_section_students(section):
    return frappe.get_all(
        "Student Group Student",
        filters={"parent": section},
        fields=["student", "student_name", "group_roll_number", "active"],
        order_by="group_roll_number asc"
    )

@frappe.whitelist()
def get_student_invoices(customer=None, company=None):
    filters = {}
    if customer:
        filters = {
            'customer': customer,
            'company': company
        }
    return frappe.get_all(
        'Sales Invoice', 
        filters=filters, 
        fields=[
        'name', 'title', 'status', 'posting_date', 'grand_total', 
        'outstanding_amount', 'customer', 'company'
        ], 
        order_by="posting_date desc"
        )

@frappe.whitelist()
def get_student_ledger(customer=None, company=None):
    filters = {
        'party_type': 'Customer',
        'is_cancelled': 0
    }
    if customer:
        filters['party'] = customer
    if company:
        filters['company'] = company

    return frappe.get_all(
        'GL Entry', 
        filters=filters, 
        fields=[
            'name', 'posting_date', 'account', 'party', 'cost_center', 
            'debit', 'credit', 'company', 'remarks', 'voucher_no', 'voucher_type'
        ], 
        order_by="posting_date asc"
    )

@frappe.whitelist()
def get_edubliss_user_session():
    try:
        return frappe.get_doc('Edubliss User Session', frappe.session.user)
    except frappe.DoesNotExistError:
        return None
    except frappe.PermissionError:
        frappe.throw(_("You do not have permission to access Edubliss User Session"), frappe.PermissionError)

@frappe.whitelist()
def get_sales_invoices(company=None):
    filters = {}
    if company:
        filters['company'] = company
    return frappe.get_all(
        'Sales Invoice', 
        filters=filters, 
        fields=['name', 'title', 'status', 'posting_date', 'grand_total', 
        'outstanding_amount', 'customer']
        )

@frappe.whitelist()
def get_students(company=None):
    filters = {}
    if company:
        filters['custom_school'] = company
    return frappe.get_all(
        'Student', 
        filters=filters, 
        fields=['student_name', 'name', 'enabled', 'custom_school', 
        'joining_date', 'student_email_id', 'image']
        )

@frappe.whitelist()
def get_teachers(company=None):
    instructors = frappe.qb.DocType("Instructor")
    employees = frappe.qb.DocType("Employee")

    instructors_query = (
        frappe.qb.from_(instructors)
        .inner_join(employees)
        .on(instructors.employee == employees.name)
        .select('*')
        .where(employees.company == company)
        .run(as_dict=1)
    )
    return instructors_query if instructors_query else []

@frappe.whitelist()
def get_parents():
    return frappe.get_all(
        'Guardian', 
        fields=['guardian_name', 'name', 'user', 'mobile_number', 
        'occupation', 'email_address', 'custom_contact_address', 'image']
        )

@frappe.whitelist()
def get_programs(company=None):
    filters = {}
    if company:
        filters['custom_school'] = company
    return frappe.get_all(
        'Program', 
        filters=filters, 
        fields=['program_name', 'name', 'program_abbreviation', 
        'custom_school', 'department', 'hero_image']
        )

@frappe.whitelist()
def get_sections(company=None):
    student_groups = frappe.qb.DocType("Student Group")
    programs = frappe.qb.DocType("Program")

    sections_query = (
        frappe.qb.from_(student_groups)
        .inner_join(programs)
        .on(student_groups.program == programs.name)
        .select('*')
        .where(programs.custom_school == company)
        .where(student_groups.group_based_on == 'Batch')
        .run(as_dict=1)
    )
    return sections_query if sections_query else []

@frappe.whitelist(allow_guest=True)
def get_company():
    schools = frappe.get_all('Company', filters={'is_group': 0}, fields=['name', 'company_name', 'abbr', 'parent_company', 'email', 'company_logo'])
    return schools

@frappe.whitelist(allow_guest=True)
def get_academic_year():
    acadyear = frappe.get_all('Academic Year', fields=['name', 'academic_year_name', 'year_start_date', 'year_end_date'])
    return acadyear

@frappe.whitelist(allow_guest=True)
def get_academic_term():
    acadterm = frappe.get_all('Academic Term', fields=['name', 'title', 'academic_year', 'term_name', 'term_start_date', 'term_end_date'])
    return acadterm

@frappe.whitelist(allow_guest=True)
def get_academic_terms(academic_year):
    try:
        if not academic_year:
            return {"message": "error", "error": "Missing academic year parameter"}
        
        terms = frappe.get_all('Academic Term', filters={'academic_year': academic_year}, fields=['name', 'title'])
        return {"message": "success", "terms": terms}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Academic Terms Error")
        return {"message": "error", "error": str(e)}

@frappe.whitelist(allow_guest=True)
def submit_form(user, user_full_name, username, company, academic_term, initial_url):
    if not (user and user_full_name and username and company and academic_term):
        frappe.local.response["type"] = "page"
        frappe.local.response["location"] = initial_url
        frappe.local.response["message"] = "Missing required fields"
        return

    try:
        # Fetch academic year for the given academic term
        academic_year = frappe.db.get_value('Academic Term', {'name': academic_term}, 'academic_year')

        if not academic_year:
            frappe.local.response["type"] = "page"
            frappe.local.response["location"] = initial_url
            frappe.local.response["message"] = "Invalid academic term"
            return

        # Fetch or create/update the user session
        user_session = frappe.get_all('Edubliss User Session', filters={'user': user}, limit=1)

        if user_session:
            # Update the existing user session
            user_session_doc = frappe.get_doc('Edubliss User Session', user_session[0].name)
            user_session_doc.school = company
            user_session_doc.academic_year = academic_year
            user_session_doc.academic_term = academic_term
            user_session_doc.save()
        else:
            # Create a new user session
            new_session = frappe.get_doc({
                'doctype': 'Edubliss User Session',
                'user': user,
                'user_full_name': user_full_name,
                'username': username,
                'school': company,
                'academic_year': academic_year,
                'academic_term': academic_term
            })
            new_session.insert()

        frappe.db.commit()

        # Redirect to the initial URL
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = initial_url
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Form Submission Error")
        frappe.local.response["type"] = "page"
        frappe.local.response["location"] = initial_url
        frappe.local.response["message"] = "An error occurred: " + str(e)

@frappe.whitelist()
def get_education_setting():
    edusetting = frappe.get_doc('Education Settings')
    return edusetting

def get_studentss():
    students = frappe.db.sql("""
        SELECT student_name, name, enabled, joining_date, student_email_id, image 
        FROM `tabStudent`
    """, as_dict=True)
    return students

@frappe.whitelist(allow_guest=True)
def get_admissions():
    today = nowdate()
    admission = frappe.get_all('Student Admission', filters={
        'published': 1,
        'enable_admission_application': 1,
        'admission_start_date': ['<=', today],
        'admission_end_date': ['>=', today]
    }, fields=[
        'name', 'title', 'route', 'academic_year',
        'admission_start_date', 'admission_end_date'
    ])
    return admission

@frappe.whitelist()
def get_students(company=None):
    filters = {}
    if company:
        filters['custom_school'] = company
    return frappe.get_all('Student', filters=filters, fields=['student_name', 'name', 'enabled', 'custom_school', 'joining_date', 'student_email_id', 'image'])

@frappe.whitelist()
def create_applicant(source_name):

    frappe.publish_realtime(
        "create_student_progress", {"progress": [1, 4]}, user=frappe.session.user
    )
    student_applicant = get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Student Applicant",
                "field_map": {
                    "name": "lead_name",
                    "custom_school": "company",
                    "program": "phone_1",
                    "academic_year": "fax_1",
                    "academic_term": "company",
                    "date_of_birth": "phone_1",
                    "fax": "fax_1",
                },
            }
        },
        ignore_permissions=True,
    )
    student_applicant.save()

    items = []
        items.append({
            's_warehouse': detail.warehouse,
            'item_code': detail.empty_bottle_item_code,
            'qty': detail.empty_bottle_qty,
            'transfer_qty': detail.empty_bottle_qty,
            'uom': detail.uom,
            'stock_uom': detail.stock_uom,
            'conversion_factor': detail.conversion_factor,
            'basic_rate': float(detail.empty_bottle_rate),
            'project': detail.project,
            'cost_center': detail.cost_center
        })
        items.append({
            's_warehouse': detail.warehouse,
            'item_code': detail.empty_bottle_item_code,
            'qty': detail.empty_bottle_qty,
            'transfer_qty': detail.empty_bottle_qty,
            'uom': detail.uom,
            'stock_uom': detail.stock_uom,
            'conversion_factor': detail.conversion_factor,
            'basic_rate': float(detail.empty_bottle_rate),
            'project': detail.project,
            'cost_center': detail.cost_center
        })

    lead = frappe.db.get_value(
        "Lead",
        source_name,
        ["student_category", "program", "academic_year"],
        as_dict=True,
    )
    student_applicant = frappe.new_doc("Student Applicant")
    student_applicant.student = lead.lead_nam
    student_applicant.student_category = lead.student_category
    student_applicant.student_name = lead.student_name
    student_applicant.program = lead.program
    student_applicant.academic_year = lead.academic_year
    student_applicant.save()

    frappe.publish_realtime(
        "create_student_progress", {"progress": [2, 4]}, user=frappe.session.user
    )
    return student_applicant
