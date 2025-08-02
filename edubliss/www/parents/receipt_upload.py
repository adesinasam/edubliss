import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b, %Y"):
    if value:
        return value.strftime(format)
    return value

def get_student_student(student):
    try:
        student_doc = frappe.get_doc('Student', student)
        return student_doc
    except Exception as e:
        return ''       

def get_context(context):
    # Ensure user is logged in
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch current user and their roles
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user
    context.user_roles = frappe.get_roles(frappe.session.user)

    # Create abbreviation from user name
    parts = current_user.full_name.split()
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # Set navigation context
    context.active_route = "parents"
    context.active_subroute = "parent_list"
    context.active_parent_route = "receipt_upload"

    # Determine docname
    docname = frappe.form_dict.get("docname")
    if not docname:
        guardian = frappe.get_list("Guardian", filters={"user": frappe.session.user}, limit_page_length=1)
        docname = guardian[0].name if guardian else None

    context.docname = docname

    # Fetch session data
    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        context.company = edubliss_session.school
        context.acadyear = edubliss_session.academic_year
        context.acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")
        context.company = context.acadyear = context.acadterm = None

    # Fetch program details
    context.program = fetch_student_program(docname, context.acadyear, context.acadterm)

    # Fetch dropdown data for company, academic year, and term
    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    # Fetch guardian and associated students
    context.parents, students = fetch_guardian_and_students(docname)

    # Process student data and generate ledger and sales information
    if students:
        process_students(context, students)

    return context


def fetch_student_program(student, academic_year, academic_term):
    try:
        return frappe.call(
            'edubliss.api.get_student_program',
            student=student,
            academic_year=academic_year,
            academic_term=academic_term
        )
    except Exception:
        return _("Welcome")


def fetch_guardian_and_students(docname):
    try:
        guardian = frappe.get_doc("Guardian", docname)
        students = guardian.get("students") if guardian else []
        return guardian, students
    except frappe.DoesNotExistError:
        frappe.throw(_("Parent not found"), frappe.DoesNotExistError)
        return None, []


def process_students(context, students):
    context.tbody_content = ""
    context.unpaid_invoices_html = ""
    context.total_debit = context.total_credit = context.balance = 0

    for student in students:
        try:
            student_doc = frappe.get_doc("Student", student.student)
            customer = student_doc.customer
        except frappe.DoesNotExistError:
            continue

        # Fetch and process ledger
        if customer:
            ledgers = frappe.call('edubliss.api.get_student_ledger', customer=customer)
            context.tbody_content += generate_ledger_html(ledgers, context)

            # Fetch and process sales orders and invoices
            sales_orders = frappe.call('edubliss.api.get_student_orders', customer=customer)

            unpaid_invoices = frappe.call('edubliss.api.get_student_unpaid_invoices', customer=customer)
            context.unpaid_invoices_html += generate_unpaid_invoices_html(unpaid_invoices,sales_orders)


def generate_ledger_html(ledgers, context):
    rows = []
    balance = context.balance

    for idx, ledger in enumerate(ledgers, start=1):
        debit = ledger.debit or 0
        credit = ledger.credit or 0
        context.total_debit += debit
        context.total_credit += credit
        balance += debit - credit


    context.balance = balance
    return ''.join(rows)


def generate_unpaid_invoices_html(unpaid_sales_invoices,sales_orders):
    
    rows = []

    for invoice in unpaid_sales_invoices:
        status_badge = get_status_badge(invoice.status)
        payment_button = f'<button class="btn btn-xs btn-danger text-2sm text-light" onclick="openModalWithFetch(\'{invoice["name"]}\',\'Sales%20Invoice\')">Pay</button>' if invoice['outstanding_amount'] > 0 else ''
        row = f"""
        <tr>            
            <td class="text-2sm">Invoice
            <input type="hidden" name="billing_document_type" value="Sales Invoice">
            </td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype=Sales%20Invoice&name={invoice['name']}" target="_blank">{invoice['name']}</a>
            <input type="hidden" name="billing_document" value="{invoice['name']}">
            </td>
            <td class="left"><a class="text-primary text-xs" href="/students/billing/{invoice['student']}">{invoice['customer']}</a></td>
            <td class="text-2sm">{frappe.format(invoice['outstanding_amount'], {'fieldtype': 'Currency'})}</td>
            <td>
            <input class="input" placeholder="Allocate Amount" value="0" type="number" name="allocated_amount" />
            </td>
            <td>{status_badge}</td>
            <td class="text-2sm">{format_date(invoice['posting_date'])}</td>
            <td class="text-2sm">{format_date(invoice['due_date'])}</td>
        </tr>
        """
        rows.append(row)
    
    return ''.join(rows)

def get_status_badge(status):
    badge_classes = {
        'Draft': 'badge-info',
        'Overdue': 'badge-danger',
        'Cancelled': 'badge-danger',
        'To Deliver and Bill': 'badge-warning',
        'Unpaid': 'badge-warning',
        'Partly Paid': 'badge-warning',
        'Completed': 'badge-success',
        'Return': 'badge-dark',
        'Paid': 'badge-success',
    }
    badge_class = badge_classes.get(status, 'badge-primary')
    return f'<div class="badge badge-sm {badge_class} badge-outline">{status}</div>'
