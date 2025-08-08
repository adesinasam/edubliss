import frappe
from frappe import _
from frappe.utils import validate_email_address
from frappe.utils.print_format import download_pdf

def on_update(doc, method):
    if doc.status == "Converted" or doc.custom_admission_status == "Offer Rejected":
        return

    try:
        # 1. Get Email Template
        edublisetting = frappe.get_doc('Edubliss Settings')
        
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
        
        # Render subject and content using Jinja
        context = {"doc": doc}
        subject = frappe.render_template(email_template.subject, context)
        
        # Handle both response and response_html
        if email_template.response_html:
            message = frappe.render_template(email_template.response_html, context)
            content_type = "html"
        else:
            message = frappe.render_template(email_template.response, context)
            content_type = "plain"

        # 4. Prepare Attachments (if applicable)
        attachments = []
        if doc.custom_admission_status == "Letter Issued":
            try:
                pdf_data = download_pdf(
                    doctype=doc.doctype,
                    name=doc.name,
                    print_format="Admission Letter",
                    as_file=True
                )
                attachments.append({
                    'fname': f"Admission_Letter_{doc.name}.pdf",
                    'fcontent': pdf_data.getvalue()
                })
            except Exception as e:
                frappe.log_error(_("Failed to generate admission letter PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

        # 5. Send Email
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            attachments=attachments if attachments else None,
            content_type=content_type,
            now=True
        )
        
        frappe.msgprint(_("Email sent successfully to: {0}").format(", ".join(recipients)))
        
    except Exception as e:
        frappe.log_error(_("Failed to send status email: {0}").format(str(e)), reference_doctype=doc.doctype, reference_name=doc.name)
        frappe.msgprint(_("Failed to send email. Please check error logs."), alert=True)