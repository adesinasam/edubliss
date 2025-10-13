import frappe
from frappe import _
from frappe.utils import get_url_to_form
from frappe.utils.print_format import download_pdf
from frappe.utils import cstr

def on_update_after_save(doc, method):
    """
    Hook that triggers after a document is updated, but only if custom_admission_status has changed
    """
    if doc.has_value_changed('custom_admission_status'):
        on_update(doc, method)

def on_update(doc, method):
    if doc.status == "Converted" or doc.custom_admission_status == "Offer Rejected":
        return

    try:
        # 1. Get Email Template and Letterhead
        edublisetting = frappe.get_doc('Edubliss Settings')
        letterhead = frappe.get_doc("Letter Head", edublisetting.letterhead) if edublisetting.letterhead else None
        
        template_map = {
            "Enquiry": edublisetting.enquiry_registration,
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

        # 2. Prepare Recipients
        recipients = []
        if doc.email_id and validate_email(doc.email_id):
            recipients.append(doc.email_id)
        if doc.custom_mothers_email and validate_email(doc.custom_mothers_email):
            recipients.append(doc.custom_mothers_email)

        if not recipients:
            frappe.msgprint(_("No valid email addresses found"), alert=True)
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
        
        # Add Fee Breakdown Template for Enquiry status
        if doc.custom_admission_status == "Enquiry" and doc.custom_program:
            try:
                # Get the fee breakdown templates from Edubliss Settings
                fee_templates = edublisetting.get("fee_breakdown_template", {})
                
                # Find the matching template based on program and student category
                matching_template = None
                for template in fee_templates:
                    if template.program == doc.custom_program:
                        if doc.student_category == "Day Student" and template.day_student_fee:
                            matching_template = template.day_student_fee
                            break
                        elif doc.student_category == "Boarder" and template.boarders_fee:
                            matching_template = template.boarders_fee
                            break
                        elif doc.student_category == "" and template.day_student_fee:
                            matching_template = template.day_student_fee
                            break
                
                if matching_template:
                    # Get the file document
                    file_doc = frappe.get_doc("File", {"file_url": matching_template})
                    pdf_data = file_doc.get_content()
                    
                    # Determine attachment filename
                    category_slug = "Boarder" if doc.student_category == "Boarder" else "Day_Student"
                    filename = f"Fee_Breakdown_{doc.custom_program}_{category_slug}_{doc.name}.pdf"
                    
                    attachments.append({
                        'fname': filename,
                        'fcontent': pdf_data
                    })
                    
            except Exception as e:
                frappe.log_error(_("Failed to attach fee breakdown template: {0}").format(str(e)), 
                               reference_doctype=doc.doctype, reference_name=doc.name)

        if doc.custom_admission_status == "Letter Issued":
            try:
                pdf_content = frappe.get_print(
                    doctype=doc.doctype,
                    name=doc.name,
                    print_format="Provisional Admission Letter"
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
        
        frappe.msgprint(_("Email sent successfully to: {0}").format(", ".join(recipients)))
        
    except Exception as e:
        frappe.log_error(_("Failed to send status email"), reference_doctype=doc.doctype, reference_name=doc.name)
        frappe.msgprint(_("Failed to send email. Please check error logs."), alert=True)

def validate_email(email):
    from frappe.utils import validate_email_address
    try:
        validate_email_address(email, throw=True)
        return True
    except:
        frappe.log_error(f"Invalid email address: {email}")
        return False

# def on_update(doc, method):
#     if doc.status == "Converted" or doc.custom_admission_status == "Offer Rejected":
#         return

#     try:
#         # 1. Get Email Template and Letterhead
#         edublisetting = frappe.get_doc('Edubliss Settings')
#         letterhead = frappe.get_doc("Letter Head", edublisetting.letterhead) if edublisetting.letterhead else None
        
#         template_map = {
#             "Enquiry": edublisetting.enquiry_registration,
#             "Form Paid": edublisetting.form_payment,
#             "Test Booked": edublisetting.test_booking,
#             "Letter Issued": edublisetting.admission_letter,
#             "Acceptance Paid": edublisetting.acceptance_paid
#         }

#         if doc.custom_admission_status not in template_map:
#             frappe.log_error(f"No template mapping for status: {doc.custom_admission_status}")
#             return

#         template_name = template_map[doc.custom_admission_status]
#         if not template_name:
#             frappe.throw(_("Email template not configured for status: {0}").format(doc.custom_admission_status))

#         # 2. Prepare Recipients
#         recipients = []
#         if doc.email_id and validate_email(doc.email_id):
#             recipients.append(doc.email_id)
#         if doc.custom_mothers_email and validate_email(doc.custom_mothers_email):
#             recipients.append(doc.custom_mothers_email)

#         if not recipients:
#             frappe.msgprint(_("No valid email addresses found"), alert=True)
#             return

#         # 3. Prepare Email
#         email_template = frappe.get_doc("Email Template", template_name)
#         subject = frappe.render_template(email_template.subject, {"doc": doc})
        
#         if email_template.use_html:
#             message = frappe.render_template(email_template.response_html, {"doc": doc})
#             # Add letterhead to HTML message
#             if letterhead:
#                 message = f"""
#                 <div style="margin-bottom: 20px;">
#                     {letterhead.content}
#                 </div>
#                 {message}
#                 """
#         else:
#             message = frappe.render_template(email_template.response, {"doc": doc})
#             # Add letterhead to plain text message
#             if letterhead:
#                 message = f"{letterhead.content}\n\n{message}"

#         # 4. Prepare Attachments (if applicable)
#         attachments = []
#         if doc.custom_admission_status == "Letter Issued":
#             try:
#                 pdf_content = frappe.get_print(
#                     doctype=doc.doctype,
#                     name=doc.name,
#                     print_format="Provisional Admission Letter"
#                 )

#                 # Convert to PDF (if not already in PDF format)
#                 pdf_data = frappe.utils.pdf.get_pdf(pdf_content)
                
#                 attachments.append({
#                     'fname': f"Provisional_Admission_Letter_{doc.name}.pdf",
#                     'fcontent': pdf_data
#                 })
#             except Exception as e:
#                 frappe.log_error(_("Failed to generate admission letter PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

#             try:
#                 pdf_contents = frappe.get_print(
#                     doctype=doc.doctype,
#                     name=doc.name,
#                     print_format="Admission Acceptance Form"
#                 )

#                 # Convert to PDF (if not already in PDF format)
#                 pdf_datas = frappe.utils.pdf.get_pdf(pdf_contents)
                
#                 attachments.append({
#                     'fname': f"Admission Acceptance Form_{doc.name}.pdf",
#                     'fcontent': pdf_datas
#                 })
#             except Exception as e:
#                 frappe.log_error(_("Failed to generate admission acceptance form PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

#         if doc.custom_admission_status == "Acceptance Paid":
#             try:
#                 pdf_content = frappe.get_print(
#                     doctype=doc.doctype,
#                     name=doc.name,
#                     print_format="Admission Letter Confirmation"
#                 )

#                 # Convert to PDF (if not already in PDF format)
#                 pdf_data = frappe.utils.pdf.get_pdf(pdf_content)
                
#                 attachments.append({
#                     'fname': f"Admission Letter Confirmation_{doc.name}.pdf",
#                     'fcontent': pdf_data
#                 })
#             except Exception as e:
#                 frappe.log_error(_("Failed to generate admission letter confirmation PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

#             if doc.student_category == "Day Student":
#                 try:
#                     # Assuming day_student_prospectus is a File field containing a PDF
#                     file_data = frappe.get_doc("File", {"file_url": edublisetting.day_student_prospectus})
#                     pdf_data = file_data.get_content()

#                     attachments.append({
#                         'fname': f"Day Student Prospectus_{doc.name}.pdf",
#                         'fcontent': pdf_data
#                     })
#                 except Exception as e:
#                     frappe.log_error(_("Failed to generate day student prospectus PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

#             if doc.student_category == "Boarder":
#                 try:
#                     # Assuming boarders_prospectus is a File field containing a PDF
#                     file_data = frappe.get_doc("File", {"file_url": edublisetting.boarders_prospectus})
#                     pdf_data = file_data.get_content()
                
#                     attachments.append({
#                         'fname': f"Boarders Prospectus_{doc.name}.pdf",
#                         'fcontent': pdf_data
#                     })
#                 except Exception as e:
#                     frappe.log_error(_("Failed to generate boarders prospectus PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

#         # 5. Send Email
#         frappe.sendmail(
#             recipients=recipients,
#             subject=subject,
#             message=message,
#             attachments=attachments if attachments else None,
#             now=True
#         )
        
#         frappe.msgprint(_("Email sent successfully to: {0}").format(", ".join(recipients)))
        
#     except Exception as e:
#         frappe.log_error(_("Failed to send status email"), reference_doctype=doc.doctype, reference_name=doc.name)
#         frappe.msgprint(_("Failed to send email. Please check error logs."), alert=True)

# def validate_email(email):
#     from frappe.utils import validate_email_address
#     try:
#         validate_email_address(email, throw=True)
#         return True
#     except:
#         frappe.log_error(f"Invalid email address: {email}")
#         return False