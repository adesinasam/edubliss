import frappe
from frappe import _
from frappe import utils
from frappe.utils import cstr, flt, getdate, nowdate
from frappe.utils import get_url_to_form
from frappe.utils.print_format import download_pdf

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

def validate_email(email):
    from frappe.utils import validate_email_address
    try:
        validate_email_address(email, throw=True)
        return True
    except:
        frappe.log_error(f"Invalid email address: {email}")
        return False

def on_update_after_save(doc, method):
    """
    Hook that triggers after a document is updated, but only if custom_admission_status has changed
    """
    if doc.has_value_changed('custom_admission_status'):
        on_update(doc, method)

def on_update(doc, method):
    if not doc.custom_is_transfer or doc.custom_admission_status == "Offer Rejected":
        return

    try:
        # 1. Get Email Template and Letterhead
        edublisetting = frappe.get_doc('Edubliss Settings')
        letterhead = frappe.get_doc("Letter Head", edublisetting.letterhead) if edublisetting.letterhead else None
        
        template_map = {
            "Enquiry": edublisetting.transferring_student,
            "Form Paid": edublisetting.form_payment,
            "Test Booked": edublisetting.test_booking,
            "Letter Issued": edublisetting.admission_letter,
            "Acceptance Paid": edublisetting.acceptance_paid
        }

        if doc.custom_admission_status not in template_map:
            frappe.log_error(f"No template mapping for status: {doc.custom_admission_status}")
            return

        template_name = template_map[doc.custom_admission_status]
        if not template_name:
            frappe.throw(_("Email template not configured for status: {0}").format(doc.custom_admission_status))

        # 2. Prepare Recipients - Get ONLY from Customer portal_users child table
        students = frappe.get_doc('Student', doc.student)
        customer_doc = frappe.get_doc('Customer', students.customer)

        # Get portal users from Customer's portal_users child table
        recipients = []
        
        if hasattr(customer_doc, 'portal_users') and customer_doc.portal_users:
            for portal_user in customer_doc.portal_users:
                if portal_user.user and validate_email(portal_user.user):
                    recipients.append(portal_user.user)
        
        if not recipients:
            frappe.msgprint(_("No valid email addresses found in Customer Portal Users"), alert=True)
            return

        # 3. Prepare Email
        email_template = frappe.get_doc("Email Template", template_name)
        subject = frappe.render_template(email_template.subject, {"doc": doc})
        
        if email_template.use_html:
            message = frappe.render_template(email_template.response_html, {"doc": doc})
            # Add letterhead to HTML message
            if letterhead:
                message = f"""
                <div style="margin-bottom: 20px;">
                    {letterhead.content}
                </div>
                {message}
                """
        else:
            message = frappe.render_template(email_template.response, {"doc": doc})
            # Add letterhead to plain text message
            if letterhead:
                message = f"{letterhead.content}\n\n{message}"

        # 4. Prepare Attachments (if applicable)
        attachments = []
        if doc.custom_admission_status == "Letter Issued":
            try:
                pdf_content = frappe.get_print(
                    doctype=doc.doctype,
                    name=doc.name,
                    print_format="Transfer - Provisional Admission Letter"
                )

                # Convert to PDF (if not already in PDF format)
                pdf_data = frappe.utils.pdf.get_pdf(pdf_content)
                
                attachments.append({
                    'fname': f"Provisional_Admission_Letter_{doc.name}.pdf",
                    'fcontent': pdf_data
                })
            except Exception as e:
                frappe.log_error(_("Failed to generate admission letter PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

            try:
                pdf_contents = frappe.get_print(
                    doctype=doc.doctype,
                    name=doc.name,
                    print_format="Admission Acceptance Form"
                )

                # Convert to PDF (if not already in PDF format)
                pdf_datas = frappe.utils.pdf.get_pdf(pdf_contents)
                
                attachments.append({
                    'fname': f"Admission Acceptance Form_{doc.name}.pdf",
                    'fcontent': pdf_datas
                })
            except Exception as e:
                frappe.log_error(_("Failed to generate admission acceptance form PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

        if doc.custom_admission_status == "Acceptance Paid":
            try:
                pdf_content = frappe.get_print(
                    doctype=doc.doctype,
                    name=doc.name,
                    print_format="Admission Letter Confirmation"
                )

                # Convert to PDF (if not already in PDF format)
                pdf_data = frappe.utils.pdf.get_pdf(pdf_content)
                
                attachments.append({
                    'fname': f"Admission Letter Confirmation_{doc.name}.pdf",
                    'fcontent': pdf_data
                })
            except Exception as e:
                frappe.log_error(_("Failed to generate admission letter confirmation PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

            if doc.student_category == "Day Student":
                try:
                    # Assuming day_student_prospectus is a File field containing a PDF
                    file_data = frappe.get_doc("File", {"file_url": edublisetting.day_student_prospectus})
                    pdf_data = file_data.get_content()

                    attachments.append({
                        'fname': f"Day Student Prospectus_{doc.name}.pdf",
                        'fcontent': pdf_data
                    })
                except Exception as e:
                    frappe.log_error(_("Failed to generate day student prospectus PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

            if doc.student_category == "Boarder":
                try:
                    # Assuming boarders_prospectus is a File field containing a PDF
                    file_data = frappe.get_doc("File", {"file_url": edublisetting.boarders_prospectus})
                    pdf_data = file_data.get_content()
                
                    attachments.append({
                        'fname': f"Boarders Prospectus_{doc.name}.pdf",
                        'fcontent': pdf_data
                    })
                except Exception as e:
                    frappe.log_error(_("Failed to generate boarders prospectus PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

        # 5. Send Email
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            attachments=attachments if attachments else None,
            now=True
        )
        
        frappe.msgprint(_("Email sent successfully to Customer Portal Users: {0}").format(", ".join(recipients)))
        
    except Exception as e:
        frappe.log_error(_("Failed to send status email"), reference_doctype=doc.doctype, reference_name=doc.name)
        frappe.msgprint(_("Failed to send email. Please check error logs."), alert=True)
