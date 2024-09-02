import frappe
from frappe import _
from frappe import utils
from frappe.utils import cstr, flt, getdate, nowdate

def setup(program_enrollment, method):
    try:
        # Lists to hold filtered courses
        all_courses = program_enrollment.courses[:]

        make_school_entry(program_enrollment)
    
        # Restore original courses
        program_enrollment.courses = all_courses

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), _("Error in setup function"))
        frappe.throw(_("An error occurred during setup: {0}").format(str(e)))

    # Return the initial program enrollment object
    return program_enrollment

def make_school_entry(program_enrollment):
    if program_enrollment.docstatus == 1:         

        # Update the existing user session
        student_doc = frappe.get_doc('Student', program_enrollment.student)
        student_doc.custom_school = program_enrollment.custom_school
        student_doc.save()

        log_doc = frappe.get_doc({
            'doctype': 'Student Log',
            'student': program_enrollment.student,
            'student_name': program_enrollment.student_name,
            'type': 'Academic',
            'date': program_enrollment.enrollment_date,
            'academic_year': program_enrollment.academic_year,
            'academic_term': program_enrollment.academic_term,
            'program': program_enrollment.program,
            'student_batch': program_enrollment.student_batch_name,
            'log': f"{program_enrollment.student_name} enrolled into {program_enrollment.program} for {program_enrollment.academic_term}"
        })
        # Insert the document into the database
        log_doc.insert()

    elif program_enrollment.docstatus == 2:
        log_doc = frappe.get_doc({
            'doctype': 'Student Log',
            'student': program_enrollment.student,
            'student_name': program_enrollment.student_name,
            'type': 'Academic',
            'date': frappe.utils.data.today(),
            'academic_year': program_enrollment.academic_year,
            'academic_term': program_enrollment.academic_term,
            'program': program_enrollment.program,
            'student_batch': program_enrollment.student_batch_name,
            'log': f"{program_enrollment.student_name} enrollment into {program_enrollment.program} cancelled."
        })
        # Insert the document into the database
        log_doc.insert()
