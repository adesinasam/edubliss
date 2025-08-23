import frappe
from frappe import _
from frappe.utils import get_url_to_form
from frappe.utils.print_format import download_pdf
from frappe.utils import cstr

def send_email_to_party(doc, method):
    if doc.payment_type != "Receive" or doc.party_type != "Customer":
        return

    try:
        # 1. Get Email Template and Letterhead
        edublisetting = frappe.get_doc('Edubliss Settings')
        letterhead = frappe.get_doc("Letter Head", edublisetting.letterhead) if edublisetting.letterhead else None
        
        template_name = edublisetting.payment_receipt
        if not template_name:
            frappe.throw(_("Email template not configured for status: Payment Receipt"))

        # 2. Prepare Recipients - Get ONLY from Customer portal_users child table
        customer_doc = frappe.get_doc('Customer', doc.party)

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
        try:
            pdf_content = frappe.get_print(
                doctype=doc.doctype,
                name=doc.name,
                print_format="Payment Entry"
            )

            # Convert to PDF (if not already in PDF format)
            pdf_data = frappe.utils.pdf.get_pdf(pdf_content)
                
            attachments.append({
                'fname': f"Payment Receipt_{doc.name}.pdf",
                'fcontent': pdf_data
            })
        except Exception as e:
            frappe.log_error(_("Failed to generate payment receipt PDF"), reference_doctype=doc.doctype, reference_name=doc.name)

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