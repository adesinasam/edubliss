
import json
import os
from werkzeug.utils import secure_filename

import frappe
from frappe import _
from frappe.utils import get_url
from frappe.email.doctype.email_group.email_group import add_subscribers
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils.dateutils import get_dates_from_timegrain
from datetime import datetime
from frappe.utils import get_files_path


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
        'docstatus': ['!=', 2]
    }
    return frappe.get_doc('Program Enrollment', filters)

@frappe.whitelist()
def get_student_groups(student, program=None, academic_term=None):
    student_group = frappe.qb.DocType("Student Group")
    student_group_students = frappe.qb.DocType("Student Group Student")

    student_group_query = (
        frappe.qb.from_(student_group)
        .inner_join(student_group_students)
        .on(student_group.name == student_group_students.parent)
        .select(student_group_students.parent)
        .where(student_group_students.student == student)
        .where(student_group.program == program)
        .where(student_group.academic_term == academic_term)
        .where(student_group.disabled == 0)
        .run(as_dict=1)
    )

    return student_group_query[0]['parent'] if student_group_query else None

@frappe.whitelist()
def get_student_lmsbatch(student, program, student_group):
    lms_batch = frappe.qb.DocType("LMS Batch")
    batch_student = frappe.qb.DocType("Batch Student")
    batch_student_group = frappe.qb.DocType("Batch Student Group")

    lms_batch_query = (
        frappe.qb.from_(lms_batch)
        .inner_join(batch_student).on(lms_batch.name == batch_student.parent)
        .inner_join(batch_student_group).on(lms_batch.name == batch_student_group.parent)
        .select(batch_student.parent)
        .where(batch_student.student == student)
        .where(lms_batch.custom_program == program)
        .where(batch_student_group.student_group == student_group)
        .run(as_dict=1)
    )

    return lms_batch_query[0]['parent'] if lms_batch_query else None

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

@frappe.whitelist(allow_guest=True)
def get_teacher_subjects(instructor, academic_term):
    return frappe.get_all(
        "Instructor Log",
        filters={"parent": instructor, "academic_term": academic_term, "course": ["!=", ""]},
        fields=["course", "academic_year", "academic_term", "program", "student_group", "department", "other_details"],
        order_by="course asc"
    )

@frappe.whitelist(allow_guest=True)
def get_teacher_sections(instructor, academic_term):
    student_group = frappe.qb.DocType("Student Group")
    student_group_instructors = frappe.qb.DocType("Student Group Instructor")

    student_group_query = (
        frappe.qb.from_(student_group)
        .inner_join(student_group_instructors)
        .on(student_group.name == student_group_instructors.parent)
        .select('*')
        .where(student_group_instructors.instructor == instructor)
        .where(student_group.academic_term == academic_term)
        .orderby(student_group.student_group_name)
        .run(as_dict=1)
    )
    return student_group_query if student_group_query else []

@frappe.whitelist(allow_guest=True)
def get_course_plan(course):
    return frappe.get_all(
        "Course Scheme of Work",
        filters={"parent": course},
        fields=["date", "terms", "week_num", "topic", "sub_topic", "objectives", "status", "periods"],
        order_by="week_num asc"
    )

@frappe.whitelist(allow_guest=True)
def get_course_plan_terms(course, terms):
    return frappe.get_all(
        "Course Scheme of Work",
        filters={
            'parent': course,
            'terms': terms
        },
        fields=["date", "terms", "week_num", "topic", "sub_topic", "objectives", "status", "periods"],
        order_by="week_num asc"
    )

@frappe.whitelist()
def get_student_due_invoices(customer=None):
    filters = {}
    if customer:
        filters = {
            'docstatus': 1,
            'customer': customer,
            'outstanding_amount': ['>',0],
            'due_date': ['<=', nowdate()]
        }
    return frappe.get_all(
        'Sales Invoice', 
        filters=filters, 
        fields=['name'], 
        limit=1
        )

@frappe.whitelist()
def get_student_unpaid_invoices(customer=None):
    filters = {}
    if customer:
        filters = {
            'docstatus': 1,
            'customer': customer,
            'outstanding_amount': ['>',0]
        }
    return frappe.get_all(
        'Sales Invoice', 
        filters=filters, 
        fields=['*'], 
        order_by="posting_date desc"
        )

@frappe.whitelist()
def get_student_invoices(customer=None):
    filters = {}
    if customer:
        filters = {
            'docstatus': 1,
            'customer': customer
        }
    return frappe.get_all(
        'Sales Invoice', 
        filters=filters, 
        fields=['*'], 
        order_by="posting_date desc",
        limit=20
        )

@frappe.whitelist()
def get_student_orders(customer=None):
    filters = {}
    if customer:
        filters = {
            'docstatus': 1,
            'customer': customer,
            'billing_status': 'Not Billed'
        }
    return frappe.get_all(
        'Sales Order', 
        filters=filters, 
        fields=['*'], 
        order_by="transaction_date desc",
        limit=20
        )

@frappe.whitelist()
def get_student_payments(customer=None):
    filters = {}
    if customer:
        filters = {
            'docstatus': 1,
            'payment_type': 'Receive',
            'party_type': 'Customer',
            'party': customer
        }
    return frappe.get_all(
        'Payment Entry', 
        filters=filters, 
        fields=['*'], 
        order_by="posting_date desc",
        limit=20
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
        frappe.qb.from_(employees)
        .inner_join(instructors)
        .on(instructors.employee == employees.name)
        .select('*')
        .where(employees.company == company)
        .where(employees.status == "Active")
        .run(as_dict=1)
    )
    return instructors_query if instructors_query else []

@frappe.whitelist()
def get_assessments(company=None, academic_term=None):
    plans = frappe.qb.DocType("Assessment Plan")
    programs = frappe.qb.DocType("Program")

    assessments_query = (
        frappe.qb.from_(plans)
        .inner_join(programs)
        .on(plans.program == programs.name)
        .select('*')
        .where(programs.custom_school == company)
        .where(plans.academic_term == academic_term)
        .where(plans.docstatus == 1)
        .run(as_dict=1)
    )
    return assessments_query if assessments_query else []

@frappe.whitelist(allow_guest=True)
def get_program_lms_batch(program=None, acadyear=None):
    return frappe.get_all('LMS Batch', 
        filters={
        'published': 1, 
        'custom_program': program, 
        'custom_academic_year': acadyear
        }, 
        fields=[
            'name', 'title', 'published', 'custom_program', 'start_date', 'end_date', 
            'custom_academic_year', 'start_time', 'end_time', 'timezone', 'description'
        ], 
        order_by="title asc")

@frappe.whitelist()
def get_course_student(course=None, academic_term=None, company=None):
    course_enrol = frappe.qb.DocType("Course Enrollment")
    program_enrol = frappe.qb.DocType("Program Enrollment")

    course_enrol_query = (
        frappe.qb.from_(course_enrol)
        .inner_join(program_enrol)
        .on(course_enrol.program_enrollment == program_enrol.name)
        .select('*')
        .where(course_enrol.course == course)
        .where(program_enrol.academic_term == academic_term)
        .where(program_enrol.custom_school == company)
        .run(as_dict=1)
    )
    return course_enrol_query if course_enrol_query else []

@frappe.whitelist()
def get_parents():
    return frappe.get_all(
        'Guardian', 
        fields=['guardian_name', 'name', 'user', 'mobile_number', 
        'occupation', 'email_address', 'custom_contact_address', 'image']
        )

@frappe.whitelist()
def get_parent_student(parent):
    return frappe.get_all(
        "Guardian Student",
        filters={"parent": parent},
        fields=["student", "student_name"]
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
def get_sections(company=None, academic_term=None):
    student_groups = frappe.qb.DocType("Student Group")
    programs = frappe.qb.DocType("Program")

    sections_query = (
        frappe.qb.from_(student_groups)
        .inner_join(programs)
        .on(student_groups.program == programs.name)
        .select('*')
        .where(programs.custom_school == company)
        .where(student_groups.academic_term == academic_term)
        .where(student_groups.group_based_on == 'Batch')
        .run(as_dict=1)
    )
    return sections_query if sections_query else []

@frappe.whitelist()
def get_program_sections(company=None, academic_term=None, course=None):
    student_groups = frappe.qb.DocType("Student Group")
    programs = frappe.qb.DocType("Program")
    program_courses = frappe.qb.DocType("Program Course")

    sections_query = (
        frappe.qb.from_(student_groups)
        .inner_join(programs).on(student_groups.program == programs.name)
        .inner_join(program_courses).on(programs.name == program_courses.parent)
        .select('*')
        .where(programs.custom_school == company)
        .where(program_courses.course == course)
        .where(student_groups.academic_term == academic_term)
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
        filters['enabled'] = 1
    return frappe.get_all('Student', filters=filters, fields=['student_name', 'name', 'enabled', 'custom_school', 'joining_date', 'student_email_id', 'image'])


@frappe.whitelist()
def create_applicant(source_name):
    frappe.publish_realtime(
        "create_applicant_progress", {"progress": [1, 4]}, user=frappe.session.user
    )
    student_applicant = get_mapped_doc(
        "Lead",
        source_name,
        {
            "Lead": {
                "doctype": "Student Applicant",
                "field_map": {
                    "name": "lead_name",
                },
            }
        },
        ignore_permissions=True,
    )

    lead = frappe.db.get_value(
        "Lead",
        source_name,
        ["company", "custom_student_email", "custom_desired_academic_year", "custom_desired_academic_term", 
         "custom_fathers_name", "custom_fathers_mobile_no", "email_id", "custom_mothers_name", 
         "custom_mothers_mobile_no", "custom_mothers_email", "custom_fathers_occupation", 
         "custom_fathers_designation", "custom_mothers_occupation", "custom_mothers_designation"],
        as_dict=True,
    )

    guardians = []

    # Create and save Father Guardian
    if lead.custom_fathers_name:
        # Check if guardian with this email already exists
        father_exists = False
        if lead.email_id:
            father_exists = frappe.db.exists("Guardian", {"email_address": lead.email_id})
        
        if not father_exists:
            student_father = frappe.new_doc("Guardian")
            student_father.guardian_name = lead.custom_fathers_name
            student_father.mobile_number = lead.custom_fathers_mobile_no
            student_father.email_address = lead.email_id
            student_father.occupation = lead.custom_fathers_occupation
            student_father.designation = lead.custom_fathers_designation
            student_father.save()
            guardian_name = student_father.name
        else:
            guardian_name = frappe.db.get_value("Guardian", {"email_address": lead.email_id}, "name")
        
        guardians.append({
            'guardian': guardian_name,
            'guardian_name': lead.custom_fathers_name,
            'relation': 'Father'
        })

    # Create and save Mother Guardian
    if lead.custom_mothers_name:
        # Check if guardian with this email already exists
        mother_exists = False
        if lead.custom_mothers_email:
            mother_exists = frappe.db.exists("Guardian", {"email_address": lead.custom_mothers_email})
        
        if not mother_exists:
            student_mother = frappe.new_doc("Guardian")
            student_mother.guardian_name = lead.custom_mothers_name
            student_mother.mobile_number = lead.custom_mothers_mobile_no
            student_mother.email_address = lead.custom_mothers_email
            student_mother.occupation = lead.custom_mothers_occupation
            student_mother.designation = lead.custom_mothers_designation
            student_mother.save()
            guardian_name = student_mother.name
        else:
            guardian_name = frappe.db.get_value("Guardian", {"email_address": lead.custom_mothers_email}, "name")
        
        guardians.append({
            'guardian': guardian_name,
            'guardian_name': lead.custom_mothers_name,
            'relation': 'Mother'
        })

    # Assign guardians to the student applicant as child document objects
    for guardian in guardians:
        student_applicant.append('guardians', guardian)

    student_applicant.custom_school = lead.company
    student_applicant.student_email_id = lead.custom_student_email
    student_applicant.academic_year = lead.custom_desired_academic_year
    student_applicant.academic_term = lead.custom_desired_academic_term
    student_applicant.application_date = nowdate()
    student_applicant.application_status = "Approved"
    student_applicant.paid = 1
    student_applicant.save()

    # Update the status of the Lead to 'Converted'
    frappe.db.set_value("Lead", source_name, "status", "Converted")
    frappe.db.commit()

    frappe.publish_realtime(
        "create_applicant_progress", {"progress": [2, 4]}, user=frappe.session.user
    )

    return student_applicant

def send_lead_status_email(doc, method):
    """Send an email using an email template when the Lead status is updated."""
    if doc.status and doc.get_db_value("status") != doc.status:
        # Fetch the email template
        email_template = frappe.get_doc("Email Template", "Lead Status Update")

        # Render the template with the Lead document
        subject = frappe.render_template(email_template.subject, {"doc": doc})
        message = frappe.render_template(email_template.response_html, {"doc": doc})

        # Send the email
        recipients = [doc.email_id]  # Assuming email_id field holds the lead's email address
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )

        frappe.msgprint(f"Email sent to {', '.join(recipients)} for status update.")

@frappe.whitelist()
def enquiry_progress(doctype, name, target_status):
    # Validate allowed doctypes for security
    allowed_doctypes = ["Lead", "Program Enrollment"]
    if doctype not in allowed_doctypes:
        frappe.throw(f"Operation not allowed for {doctype}")
    
    try:
        doc = frappe.get_doc(doctype, name)
        doc.custom_admission_status = target_status
        doc.save()
        frappe.db.commit()
        return True
    except Exception as e:
        frappe.log_error(f"Error in enquiry_progress: {str(e)}")
        frappe.throw("Failed to update status")
        return False

@frappe.whitelist()
def get_course_schedule_for_student(program_name, student_groups):
    student_groups = [sg.get("label") for sg in student_groups]

    schedule = frappe.db.get_list(
        "Course Schedule",
        fields=[
            "schedule_date",
            "room",
            "class_schedule_color",
            "course",
            "from_time",
            "to_time",
            "instructor",
            "title",
            "name",
        ],
        filters={"program": program_name, "student_group": ["in", student_groups]},
        order_by="schedule_date asc",
    )
    return schedule

@frappe.whitelist(allow_guest=True)
def get_course_schedule(course, academic_term):
    events = frappe.get_all(
        "Course Schedule",
        fields=[
            "schedule_date",
            "room",
            "class_schedule_color",
            "course",
            "custom_academic_year",
            "custom_academic_term",
            "from_time",
            "to_time",
            "instructor",
            "title",
            "name",
            "color"
        ],
        filters={"course": course, "custom_academic_term": academic_term}
    )
    
    # Transforming the data to match FullCalendar's event format
    event_list = []
    for event in events:
        start_datetime = f"{event.schedule_date} {event.from_time}"
        end_datetime = f"{event.schedule_date} {event.to_time}"

        # Convert to datetime object
        startdatetime_obj = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        enddatetime_obj = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

        # Convert to ISO 8601 format
        formatted_startdatetime = startdatetime_obj.isoformat()
        formatted_endstartdatetime = enddatetime_obj.isoformat()
        
        event_list.append({
            'id': event.name,
            'title': event.course,
            'start': formatted_startdatetime,
            'end': formatted_endstartdatetime,
            'color': set_hex_color(event)  # Set color based on the class_schedule_color
        })

    return {'message': event_list}


@frappe.whitelist(allow_guest=True)
def get_section_schedule(student_group, academic_term):
    events = frappe.get_all(
        "Course Schedule",
        fields=[
            "schedule_date",
            "room",
            "class_schedule_color",
            "course",
            "custom_academic_year",
            "custom_academic_term",
            "from_time",
            "to_time",
            "instructor",
            "title",
            "name",
            "student_group"
        ],
        filters={"student_group": student_group, "custom_academic_term": academic_term}
    )

    # Transforming the data to match FullCalendar's event format
    event_list = []
    for event in events:
        start_datetime = f"{event.schedule_date} {event.from_time}"
        end_datetime = f"{event.schedule_date} {event.to_time}"

        # Convert to datetime object
        startdatetime_obj = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        enddatetime_obj = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

        event_list.append({
            'id': event.name,
            'title': event.course,
            'start': startdatetime_obj,
            'end': enddatetime_obj,
            'color': set_hex_color(event)  # Set color based on the class_schedule_color
        })

    return {'message': event_list}

@frappe.whitelist(allow_guest=True)
def get_teacher_schedule(instructor, academic_term):
    events = frappe.get_all(
        "Course Schedule",
        fields=[
            "schedule_date",
            "room",
            "class_schedule_color",
            "course",
            "custom_academic_year",
            "custom_academic_term",
            "from_time",
            "to_time",
            "instructor",
            "title",
            "name",
            "student_group"
        ],
        filters={"instructor": instructor, "custom_academic_term": academic_term}
    )
    
    # Transforming the data to match FullCalendar's event format
    event_list = []
    # Transforming the data to match FullCalendar's event format
    event_list = []
    for event in events:
        start_datetime = f"{event.schedule_date} {event.from_time}"
        end_datetime = f"{event.schedule_date} {event.to_time}"

        # Convert to datetime object
        startdatetime_obj = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        enddatetime_obj = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")

        event_list.append({
            'id': event.name,
            'title': event.course,
            'start': startdatetime_obj,
            'end': enddatetime_obj,
            'color': set_hex_color(event)  # Set color based on the class_schedule_color
        })

    return {'message': event_list}

# Function to set hex color based on the class_schedule_color
def set_hex_color(event):
    colors = {
        "blue": "#449CF0",
        "green": "#00d420",
        "red": "#CB2929",
        "orange": "#EC864B",
        "yellow": "#dbdb02",
        "teal": "#008080",
        "violet": "#805df0",
        "cyan": "#00dede",
        "amber": "#f2b600",
        "pink": "#f051b3",
        "purple": "#af4ff0",
    }
    return colors.get(event.class_schedule_color, "#00d420")  # Default to green

@frappe.whitelist(allow_guest=True)
def get_schedule_details(event_id):
    # Fetch the event details based on the event ID (name)
    event = frappe.get_doc("Course Schedule", event_id)
    
    # Return relevant event details
    return {
        'id': event.name,
        'title': event.title,
        'start': event.schedule_date,
        'from_time': event.from_time,
        'to_time': event.to_time,
        'color': event.class_schedule_color,
        'room': event.room,
        'course': event.course,
        'custom_academic_year': event.custom_academic_year,
        'custom_academic_term': event.custom_academic_term,
        "instructor": event.instructor,
        "student_group": event.student_group
    }

@frappe.whitelist(allow_guest=True)
def get_student_attendance(student_group, student):
    events = frappe.get_all(
        "Student Attendance",
        fields=[
            "date",
            "student",
            "student_name",
            "status",
            "leave_application",
            "name",
            "student_group"
        ],
        filters={"student_group": student_group, "student": student}
    )

    # Transforming the data to match FullCalendar's event format
    event_list = []
    for event in events:
        if event.status == 'Present':
            status_name = 'P'
        elif event.status == 'Absent':
            status_name = 'A'
        elif event.status == 'Leave':
            status_name = 'L'
        else:
            status_name = ''

        from_time = '08:00:00'
        to_time = '14:00:00'
        start_datetime = f"{event.date}"
        end_datetime = f"{event.date}"

        # Convert to datetime object
        startdatetime_obj = datetime.strptime(start_datetime, "%Y-%m-%d")
        enddatetime_obj = datetime.strptime(end_datetime, "%Y-%m-%d")

        event_list.append({
            'id': event.name,
            'title': status_name,
            'start': startdatetime_obj,
            'end': enddatetime_obj,
            'color': '#fffff',
            'allDay': 'true'

        })

    return {'message': event_list}

@frappe.whitelist()
def get_order_details(order_name):
    order = frappe.get_doc('Sales Order', order_name)
    if order:
        advance_paid = order.advance_paid or 0
        outstanding_amount = order.grand_total - advance_paid
        return {
            'name': order.name,
            'customer': order.customer,
            'transaction_date': order.transaction_date,
            'student': order.student,
            'program': order.program,
            'academic_year': order.academic_year,
            'academic_term': order.academic_term,
            'grand_total': outstanding_amount
        }
    else:
        return {'error': 'Order not found'}

@frappe.whitelist()
def get_invoice_details(order_name):
    order = frappe.get_doc('Sales Invoice', order_name)
    if order:
        return {
            'name': order.name,
            'customer': order.customer,
            'transaction_date': order.posting_date,
            'student': order.student,
            'program': order.program,
            'academic_year': order.academic_year,
            'academic_term': order.academic_term,
            'grand_total': order.outstanding_amount
        }
    else:
        return {'error': 'Order not found'}

@frappe.whitelist()
def get_assessment_structure(course):
    """Returns Assessmemt Structure and their Weightage from Course Master.

    :param Course: Course
    """
    return frappe.get_all(
        "Assessment Structure",
        fields=["week", "assessment_type", "assessment_criteria", "topics", "weightage", "description", "max_score"],
        filters={"parent": course},
        order_by="idx",
    )

@frappe.whitelist()
def get_student_group_students(student_group, include_inactive=0):
    """Returns List of student, student_name in Student Group.

    :param student_group: Student Group.
    """
    if include_inactive:
        students = frappe.get_all(
            "Student Group Student",
            fields=["student", "student_name"],
            filters={"parent": student_group},
            order_by="group_roll_number",
        )
    else:
        students = frappe.get_all(
            "Student Group Student",
            fields=["student", "student_name"],
            filters={"parent": student_group, "active": 1},
            order_by="group_roll_number",
        )
    return students


@frappe.whitelist()
def get_assessment_students(assessment_plan, student_group):
    student_list = get_student_group_students(student_group)
    for i, student in enumerate(student_list):
        result = get_result(student.student, assessment_plan)
        if result:
            student_result = {}
            for d in result.custom_structure_detail:
                student_result.update({d.assessment_type: [cstr(d.score), d.grade]})
            student_result.update(
                {"total_score": [cstr(result.total_score), result.grade], "comment": result.comment}
            )
            student.update(
                {
                    "assessment_details": student_result,
                    "docstatus": result.docstatus,
                    "name": result.name,
                }
            )
        else:
            student.update({"assessment_details": None})
    return student_list

@frappe.whitelist()
def get_assessment_details(assessment_plan):
    """Returns Assessment Criteria  and Maximum Score from Assessment Plan Master.

    :param Assessment Plan: Assessment Plan
    """
    return frappe.get_all(
        "Assessment Plan Criteria",
        fields=["assessment_criteria", "maximum_score", "docstatus"],
        filters={"parent": assessment_plan},
        order_by="idx",
    )

@frappe.whitelist()
def get_assessment_structure_details(assessment_plan):
    """Returns Assessment Criteria  and Maximum Score from Assessment Plan Master.

    :param Assessment Plan: Assessment Plan
    """
    return frappe.get_all(
        "Assessment Plan Structure",
        fields=["assessment_type", "assessment_criteria", "max_score", "weightage", "topics", "docstatus"],
        filters={"parent": assessment_plan},
        order_by="idx",
    )

@frappe.whitelist()
def get_result(student, assessment_plan):
    """Returns Submitted Result of given student for specified Assessment Plan

    :param Student: Student
    :param Assessment Plan: Assessment Plan
    """
    results = frappe.get_all(
        "Assessment Result",
        filters={
            "student": student,
            "assessment_plan": assessment_plan,
            "docstatus": ("!=", 2),
        },
    )
    if results:
        return frappe.get_doc("Assessment Result", results[0])
    else:
        return None

@frappe.whitelist()
def get_grade(grading_scale, percentage):
    """Returns Grade based on the Grading Scale and Score.

    :param Grading Scale: Grading Scale
    :param Percentage: Score Percentage Percentage
    """
    grading_scale_intervals = {}
    if not hasattr(frappe.local, "grading_scale"):
        grading_scale = frappe.get_all(
            "Grading Scale Interval",
            fields=["grade_code", "threshold"],
            filters={"parent": grading_scale},
        )
        frappe.local.grading_scale = grading_scale
    for d in frappe.local.grading_scale:
        grading_scale_intervals.update({d.threshold: d.grade_code})
    intervals = sorted(grading_scale_intervals.keys(), key=float, reverse=True)
    
    grade = ""  # Initialize grade with a default value
    for interval in intervals:
        if flt(percentage) >= interval:
            grade = grading_scale_intervals.get(interval)
            break
    
    return grade

# def get_grade(grading_scale, percentage):
#     """Returns Grade based on the Grading Scale and Score.

#     :param Grading Scale: Grading Scale
#     :param Percentage: Score Percentage Percentage
#     """
#     grading_scale_intervals = {}
#     if not hasattr(frappe.local, "grading_scale"):
#         grading_scale = frappe.get_all(
#             "Grading Scale Interval",
#             fields=["grade_code", "threshold"],
#             filters={"parent": grading_scale},
#         )
#         frappe.local.grading_scale = grading_scale
#     for d in frappe.local.grading_scale:
#         grading_scale_intervals.update({d.threshold: d.grade_code})
#     intervals = sorted(grading_scale_intervals.keys(), key=float, reverse=True)
#     for interval in intervals:
#         if flt(percentage) >= interval:
#             grade = grading_scale_intervals.get(interval)
#             break
#         else:
#             grade = ""
#     return grade

@frappe.whitelist()
def get_grade_remark(grading_scale, percentage):
    """Returns Grade based on the Grading Scale and Score.

    :param Grading Scale: Grading Scale
    :param Percentage: Score Percentage Percentage
    """
    grading_scale_intervals = {}
    if not hasattr(frappe.local, "grading_scale"):
        grading_scale = frappe.get_all(
            "Grading Scale Interval",
            fields=["grade_code", "threshold", "grade_description"],
            filters={"parent": grading_scale},
        )
        frappe.local.grading_scale = grading_scale
    for d in frappe.local.grading_scale:
        grading_scale_intervals.update({d.threshold: d.grade_description})
    intervals = sorted(grading_scale_intervals.keys(), key=float, reverse=True)
    for interval in intervals:
        if flt(percentage) >= interval:
            grade = grading_scale_intervals.get(interval)
            break
        else:
            grade = ""
    return grade

@frappe.whitelist()
def mark_assessment_result(assessment_plan, scores):
    student_score = json.loads(scores)
    assessment_details = []
    assessment_details_type = []
    total_weightage_score = 0  # Initialize total weightage score

    plans = frappe.get_doc("Assessment Plan", assessment_plan)
    grading_scale = plans.grading_scale

    # Get assessment structures only once
    structures = frappe.get_all(
        "Assessment Plan Structure",
        fields=["assessment_type", "assessment_criteria", "max_score", "weightage", "topics", "docstatus"],
        filters={"parent": assessment_plan},
        order_by="idx",
    )

    # Initialize a dictionary to hold the sum of weightage_score for each assessment_criteria
    weightage_score_sum = {}

    for criteria in student_score.get("assessment_details"):
        # Find the matching structure for the current criteria based on assessment_type
        matching_structure = next((s for s in structures if s.assessment_type == criteria), None)

        # Get the score for the current criterion
        score = flt(student_score["assessment_details"][criteria])
        
        # Initialize weightage_score as 0 to avoid reference before assignment
        weightage_score = 0

        if matching_structure:
            maximum_score = matching_structure.max_score if matching_structure else 0
            weightage = matching_structure.weightage if matching_structure else 0

            # Calculate weightage score
            weightage_score = (score / maximum_score) * weightage if maximum_score else 0

            # Calculate percentage score
            percentage = (score / maximum_score) * 100 if maximum_score else 0

            # Accumulate total weightage score
            total_weightage_score += weightage_score

            # Sum weightage_score for each assessment_criteria
            if matching_structure.assessment_criteria in weightage_score_sum:
                weightage_score_sum[matching_structure.assessment_criteria] += weightage_score
            else:
                weightage_score_sum[matching_structure.assessment_criteria] = weightage_score

        grade=get_grade(grading_scale, percentage)    

        assessment_details.append(
            {
                "assessment_type": criteria,  # Maintain original mapping
                "score": score,
                "assessment_criteria": matching_structure.assessment_criteria if matching_structure else None,
                "topics": matching_structure.topics if matching_structure else None,
                "maximum_score": maximum_score,
                "weightage": weightage,
                "weightage_score": weightage_score,
                "grade": grade
            }
        )

    details=frappe.get_all(
        "Assessment Plan Criteria",
        fields=["assessment_criteria", "maximum_score", "docstatus"],
        filters={"parent": assessment_plan},
        order_by="idx",
    )
    # Prepare details for updating
    for matching_detail in details:
        assessment_criteria = matching_detail.assessment_criteria
        assessment_details_type.append(
            {
                "assessment_criteria": assessment_criteria,
                "score": weightage_score_sum.get(assessment_criteria, 0)  # Use the weightage sum for this criteria
            }
        )

    # Get the Assessment Result document and update with new data
    assessment_result = get_assessment_result_doc(
        student_score["student"], assessment_plan
    )
    assessment_result.update(
        {
            "student": student_score.get("student"),
            "assessment_plan": assessment_plan,
            "comment": student_score.get("comment"),
            "total_score": total_weightage_score,  # Add the total weightage score
            "custom_structure_detail": assessment_details,
            "details": assessment_details_type,
        }
    )
    assessment_result.save()
    
    custom_structure_detail = {}
    for d in assessment_result.custom_structure_detail:
        custom_structure_detail.update({d.assessment_type: d.grade})

    assessment_result_dict = {
        "name": assessment_result.name,
        "student": assessment_result.student,
        "total_score": assessment_result.total_score,
        "grade": assessment_result.grade,
        "custom_structure_detail": custom_structure_detail,
    }

    return assessment_result_dict

# def get_assessment_result_doc(student, assessment_plan):
#     assessment_result = frappe.get_all(
#         "Assessment Result",
#         filters={
#             "student": student,
#             "assessment_plan": assessment_plan,
#             "docstatus": ("!=", 2),
#         },
#     )
#     if assessment_result:
#         doc = frappe.get_doc("Assessment Result", assessment_result[0])
#         if doc.docstatus == 0:
#             return doc
#         elif doc.docstatus == 1:
#             frappe.msgprint(_("Result already Submitted"))
#             return None
#     else:
#         return frappe.new_doc("Assessment Result")

def get_assessment_result_doc(student, assessment_plan):
    assessment_result = frappe.get_all(
        "Assessment Result",
        filters={
            "student": student,
            "assessment_plan": assessment_plan,
            "docstatus": ("!=", 2),  # Exclude cancelled
        },
    )
    if assessment_result:
        doc = frappe.get_doc("Assessment Result", assessment_result[0].name)
        if doc.docstatus == 0:
            return doc  # Update existing draft
        elif doc.docstatus == 1:
            frappe.throw(_("Result already submitted for this student and assessment plan."), title="Duplicate Entry")
    else:
        return frappe.new_doc("Assessment Result")

# @frappe.whitelist()
# def add_guardian_to_customer_portal(student_id):

#     frappe.publish_realtime(
#         "create_guardian_progress", {"progress": [1, 4]}, user=frappe.session.user
#     )

#     student = frappe.get_doc("Student", student_id)
#     customer = student.customer  # Assuming the field is named "customer"
#     customer_doc = frappe.get_doc("Customer", customer) 

#     if not customer:
#         frappe.throw("No customer linked to this student")
#     if not student.guardians:
#         frappe.msgprint(f"No guardians found for student {student_id}")
#         return
    
#     added_users = []
#     skipped_users = []

#     guardians = student.get("guardians")  # Assuming the child table is named "guardians"

#     for guardian in guardians:
#         guardian_doc = frappe.get_doc("Guardian", guardian.guardian)

#         if not guardian_doc.email_address:
#             skipped_users.append(f"{guardian_doc.guardian_name} (no email)")
#             continue
        
#         # Check if user exists or create new
#         if not frappe.db.exists("User", guardian_doc.email_address):
#             try:
#                 user = frappe.get_doc({
#                     "doctype": "User",
#                     "email": guardian_doc.email_address,
#                     "first_name": guardian_doc.guardian_name,
#                     "send_welcome_email": 1,
#                     "role_profile_name": "MPIS Parent",
#                     "user_type": "Website User"
#                 }).insert(ignore_permissions=True)
#                 user_name = user.name
#             except Exception as e:
#                 skipped_users.append(f"{guardian_doc.guardian_name} (error: {str(e)})")
#                 continue
#         else:
#             user_name = frappe.db.get_value("User", guardian_doc.email_address, "name")
        
#         # Check if already in portal users
#         existing = [d.user for d in customer_doc.portal_users or []]
#         if user_name in existing:
#             skipped_users.append(f"{user_name} (already exists)")
#             continue
        
#         # Append to portal_users child table
#         customer_doc.append("portal_users", {
#             "user": user_name
#         })
#         added_users.append(user_name)

#     frappe.publish_realtime(
#         "create_guardian_progress", {"progress": [4, 4]}, user=frappe.session.user
#     )
    
#     if added_users:
#         try:
#             customer_doc.save(ignore_permissions=True)
#             frappe.db.commit()
#             message = f"Successfully added {len(added_users)} guardian(s) as portal users"
#             if skipped_users:
#                 message += f"<br>Skipped {len(skipped_users)}: {', '.join(skipped_users)}"
#             frappe.msgprint(message)
#         except Exception as e:
#             frappe.msgprint(f"Error saving student: {str(e)}", alert=True)
#     else:
#         frappe.msgprint("No new guardians were added. " + 
#                        (f"Skipped: {', '.join(skipped_users)}" if skipped_users else ""))

@frappe.whitelist()
def add_guardian_to_customer_portal(student_id):
    frappe.publish_realtime(
        "create_guardian_progress", {"progress": [1, 5]}, user=frappe.session.user
    )

    student = frappe.get_doc("Student", student_id)
    
    # Step 1: Create User for Student if not exists and user field is not set
    if not student.user and student.student_email_id:
        frappe.publish_realtime(
            "create_guardian_progress", {"progress": [2, 5]}, user=frappe.session.user
        )
        
        if not frappe.db.exists("User", student.student_email_id):
            try:
                student_user = frappe.get_doc({
                    "doctype": "User",
                    "email": student.student_email_id,
                    "first_name": student.first_name or student.student_name,
                    "last_name": student.last_name or "",
                    "send_welcome_email": 0,
                    # "role_profile_name": "MPIS Student",  # Adjust role profile as needed
                    "user_type": "Website User"
                }).insert(ignore_permissions=True)
                
                # Update student with created user
                student.user = student_user.name
                student.save(ignore_permissions=True)
                frappe.db.commit()
                
                frappe.msgprint(f"Created user for student: {student_user.name}")
                
            except Exception as e:
                frappe.msgprint(f"Error creating user for student: {str(e)}", alert=True)
        else:
            # User exists but not linked to student
            student.user = student.student_email_id
            student.save(ignore_permissions=True)
            frappe.db.commit()

    frappe.publish_realtime(
        "create_guardian_progress", {"progress": [3, 5]}, user=frappe.session.user
    )

    customer = student.customer  # Assuming the field is named "customer"
    if not customer:
        frappe.throw("No customer linked to this student")
    
    customer_doc = frappe.get_doc("Customer", customer)

    if not student.guardians:
        frappe.msgprint(f"No guardians found for student {student_id}")
        return
    
    added_users = []
    skipped_users = []

    guardians = student.get("guardians")  # Assuming the child table is named "guardians"

    for guardian in guardians:
        guardian_doc = frappe.get_doc("Guardian", guardian.guardian)

        if not guardian_doc.email_address:
            skipped_users.append(f"{guardian_doc.guardian_name} (no email)")
            continue
        
        # Check if user exists or create new
        if not frappe.db.exists("User", guardian_doc.email_address):
            try:
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": guardian_doc.email_address,
                    "first_name": guardian_doc.guardian_name,
                    "send_welcome_email": 1,
                    "role_profile_name": "MPIS Parent",
                    "user_type": "Website User"
                }).insert(ignore_permissions=True)
                user_name = user.name
            except Exception as e:
                skipped_users.append(f"{guardian_doc.guardian_name} (error: {str(e)})")
                continue
        else:
            user_name = frappe.db.get_value("User", guardian_doc.email_address, "name")
        
        # Check if already in portal users
        existing = [d.user for d in customer_doc.portal_users or []]
        if user_name in existing:
            skipped_users.append(f"{user_name} (already exists)")
            continue
        
        # Append to portal_users child table
        customer_doc.append("portal_users", {
            "user": user_name
        })
        added_users.append(user_name)

    frappe.publish_realtime(
        "create_guardian_progress", {"progress": [5, 5]}, user=frappe.session.user
    )
    
    if added_users:
        try:
            customer_doc.save(ignore_permissions=True)
            frappe.db.commit()
            message = f"Successfully added {len(added_users)} guardian(s) as portal users"
            if skipped_users:
                message += f"<br>Skipped {len(skipped_users)}: {', '.join(skipped_users)}"
            frappe.msgprint(message)
        except Exception as e:
            frappe.msgprint(f"Error saving customer: {str(e)}", alert=True)
    else:
        frappe.msgprint("No new guardians were added. " + 
                       (f"Skipped: {', '.join(skipped_users)}" if skipped_users else ""))


@frappe.whitelist()
def upload_receipt_form():
    try:
        # Get form data
        form_dict = frappe.local.form_dict
        initial_url = form_dict.get('initial_url')
        amount_paid = flt(form_dict.get('amount_paid'))
        
        # Validate required fields
        required_fields = ['posting_date', 'amount_paid', 'depositor']
        for field in required_fields:
            if not form_dict.get(field):
                return error_response(initial_url, f"{field.replace('_', ' ').title()} is required")
        
        # Add invoice allocations
        invoice_names = frappe.request.form.getlist('billing_document')
        allocate_amounts = frappe.request.form.getlist('allocated_amount')
        
        if len(invoice_names) != len(allocate_amounts):
            return error_response(initial_url, "Mismatch between invoice names and allocated amounts")
        
        billing_receipts = []
        total_allocated = 0
        
        for i, invoice_name in enumerate(invoice_names):
            allocated_amount = flt(allocate_amounts[i])
            if allocated_amount > 0:
                billing_receipts.append({
                    "billing_document_type": "Sales Invoice",
                    "billing_document": invoice_name,
                    "allocated_amount": allocated_amount
                })
                total_allocated += allocated_amount
        
        # Validate allocation matches amount paid
        if abs(total_allocated - amount_paid) > 0.01:  # Allow small rounding differences
            return error_response(initial_url, f"Total allocated amount ({total_allocated}) does not match amount paid ({amount_paid})")

        # Validate amount
        if amount_paid <= 0:
            return error_response(initial_url, "Amount Paid must be greater than 0")
        
        # File handling
        file = frappe.request.files.get('avatar')
        if not file or file.filename == '':
            return error_response(initial_url, "Please select a valid image file (PNG/JPG/JPEG)")
        
        # Validate file extension
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        filename = secure_filename(file.filename)
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return error_response(initial_url, "Invalid file type. Only PNG, JPG, JPEG allowed")

        # Create Payment Receipt document FIRST
        receipt_doc = frappe.get_doc({
            "doctype": "Payment Receipt Upload",
            "posting_date": getdate(form_dict.get('posting_date')),
            "paid_amount": amount_paid,
            "billing_receipts": billing_receipts,
            "depositor_name": form_dict.get('depositor'),
            "user_name": form_dict.get('user_name'),
            "is_portal": 1,
            "status": "Pending"
        })
        receipt_doc.insert(ignore_permissions=True)
        
        # Now handle file attachment with proper reference
        file_content = file.stream.read()
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "attached_to_doctype": "Payment Receipt Upload",
            "attached_to_name": receipt_doc.name,  # This was missing
            "attached_to_field": "receipt_image",
            "content": file_content,  # Direct upload instead of saving to filesystem
            "is_private": 0
        })
        file_doc.insert(ignore_permissions=True)
        
        # Update receipt with file URL
        receipt_doc.db_set('attach_image', file_doc.file_url)
        
        frappe.db.commit()
        return success_response(initial_url, "?success=1")
        
    except Exception as e:
        frappe.log_error(f"Receipt upload failed: {str(e)}")
        frappe.db.rollback()
        return error_response(initial_url, f"An error occurred: {str(e)}")

def success_response(redirect_url, message):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = redirect_url + message

def error_response(redirect_url, message):
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = redirect_url + "?error=" + frappe.utils.quote(message)


@frappe.whitelist()
def update_transfer_status(enrollment_tool_doc):
    """
    Update is_transfer = 1 for program enrollments created by the enrollment tool
    """
    doc = frappe.parse_json(enrollment_tool_doc) if isinstance(enrollment_tool_doc, str) else enrollment_tool_doc
    
    # Get all students from the enrollment tool
    students = doc.get('students', [])
    
    if not students:
        frappe.msgprint(_("No students found to update transfer status"))
        return
    
    updated_count = 0
    
    for stud in students:
        if stud.get('student'):
            # Find the program enrollment that matches the criteria
            enrollment_filters = {
                'student': stud.get('student'),
                'student_category': stud.get('student_category'),
                'program': doc.get('new_program'),
                'academic_term': doc.get('new_academic_term'),
                'academic_year': doc.get('new_academic_year')
            }
            
            # Remove None values from filters
            enrollment_filters = {k: v for k, v in enrollment_filters.items() if v is not None}
            
            # Find the program enrollment
            enrollment = frappe.get_all(
                'Program Enrollment',
                filters=enrollment_filters,
                fields=['name'],
                order_by='creation desc',  # Get the most recent one
                limit=1
            )
            
            if enrollment:
                # Update the is_transfer field
                frappe.db.set_value(
                    'Program Enrollment',
                    enrollment[0]['name'],
                    'custom_is_transfer',
                    1
                )
                updated_count += 1
    
    frappe.msgprint(_("Transfer status updated for {0} program enrollments").format(updated_count))

@frappe.whitelist()
def get_subjects_schedule_instructors(course, academic_term, student_group):
    # Find instructors that have a matching Instructor Log row
    instructors = frappe.db.sql("""
        SELECT DISTINCT i.name
        FROM `tabInstructor` i
        JOIN `tabInstructor Log` il ON il.parent = i.name
        WHERE il.course = %s
          AND il.academic_term = %s
          AND il.student_group = %s
    """, (course, academic_term, student_group), as_dict=True)

    return [i.name for i in instructors]

@frappe.whitelist()
def get_instructors(student_group):
    return frappe.get_all(
        "Student Group Instructor", {"parent": student_group}, pluck="instructor"
    )

@frappe.whitelist()
def get_class_schedule(student_group):
    filters = {
        "student_group": student_group,
        "docstatus": 1
    }
    found = frappe.get_all("Class Schedule", 
        filters=filters, 
        fields=["name"], 
        limit_page_length=1
        )
    if not found:
        return None
    return found[0].get("name")

@frappe.whitelist()
def get_subject_schedules(schedule):
    return frappe.get_all(
        "Subject Schedule",
        filters={"parent": schedule},
        fields=["name", "course", "student_group", "week_days", "period_label", "instructor", "instructor_name", "room", "from_time", "to_time", "is_cancelled", "class_schedule_color"]
    )

@frappe.whitelist()
def get_timetable_slots(schedule):
    return frappe.get_all(
        "Timetable Slot",
        filters={"parent": schedule},
        fields=["name", "period_label", "label", "is_break", "duration", "start_time", "end_time"],
        order_by="idx asc"
    )

frappe.whitelist()
def get_instructor_class_schedule(instructor=None,academic_term=None):
    filters = {
        "instructor": instructor,
        "academic_term": academic_term
    }
    found = frappe.get_all("Subject Schedule", 
        filters=filters, 
        fields=["parent"], 
        limit_page_length=1
        )
    if not found:
        return None
    return found[0].get("parent")

@frappe.whitelist()
def get_instructor_subject_schedules(instructor=None,academic_term=None):
    return frappe.get_all(
        "Subject Schedule",
        filters={
        "instructor": instructor,
        "academic_term": academic_term
        },
        fields=["name", "course", "student_group", "week_days", "period_label", "instructor", "instructor_name", "room", "from_time", "to_time", "is_cancelled", "class_schedule_color"]
    )

@frappe.whitelist(allow_guest=True)
def get_lead_details(admission_enquiry_no):
    if not admission_enquiry_no:
        return {"error": "No admission_enquiry_no provided"}

    lead = frappe.get_doc("Lead", admission_enquiry_no)

    return {
        "admission_enquiry_no": admission_enquiry_no,
        "student_first_name": lead.first_name or "",
        "student_middle_name": lead.middle_name or "",
        "student_last_name": lead.last_name or "",
        "student_full_name": lead.lead_name 
            or f"{(lead.first_name or '').strip()} {(lead.last_name or '').strip()}".strip(),
        "program": lead.program,
        "gender": lead.gender,
        "academic_year": lead.custom_desired_academic_year,
        "academic_term": lead.custom_desired_academic_term,
        "birth_certificate": lead.custom_birth_certificate,
        "applicants_passport": lead.custom_applicants_passport,
        "immunization_card": lead.custom_imm,
        "fathers_passport": lead.custom_fathers_passport,
        "mothers_passport": lead.custom_mothers_passport,
        "emergency_contact_passport": lead.custom_emergency_contact_passport,
        "fathers_id_card": lead.custom_fathers_id_card,
        "mothers_id_card": lead.custom_mothers_id_card,
        "previous_school_result": lead.custom_previous_school_result,
        "transfer_certificate": lead.custom_transfer_certificate
    }
