import frappe
from frappe import _
from datetime import datetime

no_cache = 1

def format_date(value, format="%d %b, %Y"):
    if value:
        return value.strftime(format)
    return value

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
    context.active_student_route = "billing"

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

    # Try to fetch the Student Program document and handle errors if it doesn't exist
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
        program_name = program.program
        context.programs = frappe.get_doc("Program", program_name)
    else:
        context.program = _("Welcome")  # or set a default value if required

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
        customer = context.students.customer
    except Exception as e:
        customer = None

    # Fetch student ledger
    ledgers = frappe.call(
        'edubliss.api.get_student_ledger', 
        customer=customer 
        )
    context.ledgers = ledgers

    # Initialize totals and balance
    total_debit = 0
    total_credit = 0
    balance = 0
    
    # Start generating the tbody content
    tbody_content = ''
    
    for index, ledger in enumerate(ledgers, start=1):
        debit = ledger.debit or 0
        credit = ledger.credit or 0
        total_debit += debit
        total_credit += credit
        balance += debit - credit
        
        tbody_content += f'''
        <tr>
            <td class="text-xs">{index}</td>
            <td class="text-xs">{format_date(ledger.posting_date)}</td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype={ledger.voucher_type}&name={ledger.voucher_no}" target="_blank">{ledger.voucher_no}</a></td>
            <td class="text-xs">{ledger.voucher_type}</td>
            <td class="text-xs">{frappe.format_value(debit, {"fieldtype": "Currency"})}</td>
            <td class="text-xs">{frappe.format_value(credit, {"fieldtype": "Currency"})}</td>
            <td class="text-xs {'text-success' if balance < 0 else 'text-gray-800'}">{frappe.format_value(balance, {"fieldtype": "Currency"})}</td>
            <td class="text-xs">{ledger.remarks}</td>
        </tr>
        '''

    context.tbody_content = tbody_content
    context.total_debit = total_debit
    context.total_credit = total_credit
    context.balance = balance

    # Fetch sales orders
    if customer:
        sales_orders = frappe.call('edubliss.api.get_student_orders', customer=customer)
        context.sales_orders_html = generate_sales_orders_html(sales_orders)

        sales_invoices = frappe.call('edubliss.api.get_student_invoices', customer=customer)
        context.sales_invoices_html = generate_sales_invoices_html(sales_invoices)

        unpaid_sales_invoices = frappe.call('edubliss.api.get_student_unpaid_invoices', customer=customer)
        context.unpaid_invoices_html = generate_unpaid_invoices_html(unpaid_sales_invoices, sales_orders)

    return context

def generate_sales_orders_html(sales_orders):
    if not sales_orders:
        return '<tr><td colspan="7" class="text-center">No Incoming Bill found.</td></tr>'
    
    rows = []
    for idx, order in enumerate(sales_orders, start=1):
        status_badge = get_status_badge(order.status)
        payment_button = f'<button class="btn btn-xs btn-dark text-2sm text-light" onclick="openModalWithFetch(\'{order['name']}\',\'Sales%20Order\')">Pay</button>' if order['advance_paid'] < order['grand_total'] else ''
        row = f"""
        <tr>
            <td class="text-2sm">{format_date(order['transaction_date'])}</td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype=Sales%20Order&name={order['name']}" target="_blank">{order['name']}</a></td>
            <td class="text-2sm">Order</td>
            <td class="text-2sm">{frappe.format(order['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td>{status_badge}</td>
            <td>{payment_button}</td>
        </tr>
        """
        rows.append(row)
    
    return ''.join(rows)

def generate_sales_invoices_html(sales_invoices):
    if not sales_invoices:
        return '<tr><td colspan="7" class="text-center">No Invoice found.</td></tr>'
    
    rows = []
    for invoice in sales_invoices:
        status_badge = get_status_badge(invoice.status)
        payment_button = f'<button class="btn btn-xs btn-danger text-2sm text-light" onclick="openModalWithFetch(\'{invoice["name"]}\',\'Sales%20Invoice\')">Pay</button>' if invoice['outstanding_amount'] > 0 else ''
        row = f"""
        <tr>
            <td class="text-2sm">{format_date(invoice['posting_date'])}</td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype=Sales%20Invoice&name={invoice['name']}" target="_blank">{invoice['name']}</a></td>
            <td class="text-2sm">{frappe.format(invoice['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{frappe.format(invoice['outstanding_amount'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{format_date(invoice['due_date'])}</td>
            <td>{status_badge}</td>
            <td>{payment_button}</td>
        </tr>
        """
        rows.append(row)
    
    return ''.join(rows)

def generate_unpaid_invoices_html(unpaid_sales_invoices, sales_orders):
    if not unpaid_sales_invoices and not sales_orders:
        return '<tr><td colspan="7" class="text-center">No Invoice found.</td></tr>'
    
    rows = []
    for idx, order in enumerate(sales_orders, start=1):
        # Skip orders where advance_paid >= grand_total
        if not (order.get('advance_paid', 0) < order.get('grand_total', 0)):
            continue  # Skip this order

        status_badge = get_status_badge(order.status)
        payment_button = f'<button class="btn btn-xs btn-dark text-2sm text-light" onclick="openModalWithFetch(\'{order['name']}\',\'Sales%20Order\')">Pay</button>' if order['advance_paid'] < order['grand_total'] else ''
        row = f"""
        <tr>
            <td class="text-2sm">{format_date(order['transaction_date'])}</td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype=Sales%20Order&name={order['name']}" target="_blank">{order['name']}</a></td>
            <td class="text-2sm">Order</td>
            <td class="text-2sm">{frappe.format(order['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{frappe.format(order['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{format_date(order['delivery_date']) or ""}</td>
            <td>{status_badge}</td>
            <td>{payment_button}</td>
        </tr>
        """
        rows.append(row)

    for invoice in unpaid_sales_invoices:
        status_badge = get_status_badge(invoice.status)
        payment_button = f'<button class="btn btn-xs btn-danger text-2sm text-light" onclick="openModalWithFetch(\'{invoice["name"]}\',\'Sales%20Invoice\')">Pay</button>' if invoice['outstanding_amount'] > 0 else ''
        row = f"""
        <tr>
            <td class="text-2sm">{format_date(invoice['posting_date'])}</td>
            <td class="text-center"><a class="text-primary text-xs" href="/printview?doctype=Sales%20Invoice&name={invoice['name']}" target="_blank">{invoice['name']}</a></td>
            <td class="text-2sm">Invoice</td>
            <td class="text-2sm">{frappe.format(invoice['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{frappe.format(invoice['outstanding_amount'], {'fieldtype': 'Currency'})}</td>
            <td class="text-2sm">{format_date(invoice['due_date'])}</td>
            <td>{status_badge}</td>
            <td>{payment_button}</td>
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
        'Partly Paid': 'badge-warning',
        'Completed': 'badge-success',
        'Return': 'badge-dark',
        'Paid': 'badge-success',
    }
    badge_class = badge_classes.get(status, 'badge-primary')
    return f'<div class="badge badge-sm {badge_class} badge-outline">{status}</div>'
