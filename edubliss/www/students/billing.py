import frappe
from frappe import _

no_cache = 1

def get_context(context):

    docname = frappe.form_dict.docname

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

    context.docname = frappe.form_dict.docname

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
    
    for index, ledger in enumerate(ledgers, start=1):
        debit = ledger.debit or 0
        credit = ledger.credit or 0
        total_debit += debit
        total_credit += credit
        balance += debit - credit
        
    context.total_debit = total_debit
    context.total_credit = total_credit
    context.balance = balance

    # Fetch sales orders
    if customer:
        sales_orders = frappe.call('edubliss.api.get_student_orders', customer=customer)
        context.sales_orders_html = generate_sales_orders_html(sales_orders)

        sales_invoices = frappe.call('edubliss.api.get_student_invoices', customer=customer)
        context.sales_invoices_html = generate_sales_invoices_html(sales_invoices)

    return context

def generate_sales_orders_html(sales_orders):
    if not sales_orders:
        return '<tr><td colspan="7" class="text-center">No Incoming Bill found.</td></tr>'
    
    rows = []
    for idx, order in enumerate(sales_orders, start=1):
        status_badge = get_status_badge(order.status)
        row = f"""
        <tr>
            <td>{idx}</td>
            <td><a class="leading-none font-semibold text-sm text-gray-900 hover:text-primary" href="/printview?doctype=Sales%20Order&name={order['name']}" target="_blank">{order['customer']}</a></td>
            <td>{status_badge}</td>
            <td>{order['transaction_date']}</td>
            <td>{frappe.format(order['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td class="text-center"><a class="btn btn-link" href="/printview?doctype=Sales%20Order&name={order['name']}" target="_blank">{order['name']}</a></td>
            <td><a class="btn btn-xs btn-dark text-2sm text-light" href="/api/method/edubliss.edubliss.payment_request.make_payment_request?dn={order['name']}&dt=Sales%20Order&submit_doc=1&amt={order['grand_total']}&order_type=Shopping%20Cart">Pay</a></td>
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
        payment_button = f'<a class="btn btn-xs btn-dark text-2sm text-light" href="/api/method/edubliss.edubliss.payment_request.make_payment_request?dn={invoice.name}&dt=Sales%20Invoice&submit_doc=1&amt={invoice['outstanding_amount']}&order_type=Shopping%20Cart">Pay</a>' if invoice['outstanding_amount'] > 0 else ''
        row = f"""
        <tr>
            <td><input class="checkbox checkbox-sm" data-datatable-row-check="true" type="checkbox" value="1"/></td>
            <td><a class="leading-none font-semibold text-sm text-gray-900 hover:text-primary" href="/printview?doctype=Sales%20Invoice&name={invoice['name']}" target="_blank">{invoice['title']}</a></td>
            <td>{status_badge}</td>
            <td>{invoice['posting_date']}</td>
            <td>{frappe.format(invoice['grand_total'], {'fieldtype': 'Currency'})}</td>
            <td>{frappe.format(invoice['outstanding_amount'], {'fieldtype': 'Currency'})}</td>
            <td class="text-center"><a class="btn btn-link" href="/printview?doctype=Sales%20Invoice&name={invoice['name']}" target="_blank">{invoice['name']}</a></td>
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
    }
    badge_class = badge_classes.get(status, 'badge-primary')
    return f'<div class="badge badge-sm {badge_class} badge-outline">{status}</div>'
