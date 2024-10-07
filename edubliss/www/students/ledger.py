import frappe
from frappe import _

no_cache = 1

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
    else:
        context.program = _("Welcome")  # or set a default value if required

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.students = frappe.get_doc("Student", docname)
        customer = context.students.customer
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

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
            <td>{index}</td>
            <td>{ledger.posting_date}</td>
            <td><span class="leading-none font-semibold text-sm text-gray-900 hover:text-primary">{ledger.party}</span></td>
            <td>{frappe.format_value(debit, {"fieldtype": "Currency"})}</td>
            <td>{frappe.format_value(credit, {"fieldtype": "Currency"})}</td>
            <td>{frappe.format_value(balance, {"fieldtype": "Currency"})}</td>
            <td>{ledger.voucher_type}</td>
            <td class="text-center"><a class="btn btn-link" href="/printview?doctype={ledger.voucher_type}&name={ledger.voucher_no}" target="_blank">{ledger.voucher_no}</a></td>
            <td>{ledger.remarks}</td>
        </tr>
        '''

    context.tbody_content = tbody_content
    context.total_debit = total_debit
    context.total_credit = total_credit
    context.balance = balance
    

    return context
