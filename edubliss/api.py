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
        'academic_term': academic_term
    }

    doc_data = frappe.get_doc('Program Enrollment', filters)
    return doc_data

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
    return frappe.get_all('Student', filters=filters, fields=['student_name', 'name', 'enabled', 'custom_school', 'joining_date', 'student_email_id', 'image'])

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
