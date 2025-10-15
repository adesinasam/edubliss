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
    context.active_student_route = "fee"

    context.docname = docname

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")
        company = None

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        students = frappe.get_doc("Student", docname)
        context.students = students
        customer = students.customer
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

    # Try to fetch the Student Program document and handle errors if it doesn't exist
    try:
        program = frappe.call(
            'edubliss.api.get_student_program',
            student=docname, 
            academic_year=acadyear, 
            academic_term=acadterm
        )
    except Exception as e:
        program = ''

    if program:
        context.program = program    
        program_name = program.program
        context.programs = frappe.get_doc("Program", program_name)
        
        # Get the fee breakdown PDF based on program and academic year
        try:
            # Get Edubliss Settings (single doctype)
            edubliss_settings = frappe.get_doc("Edubliss Settings")
            
            # Find the matching fee breakdown template
            fee_breakdown = None
            for row in edubliss_settings.get("fee_breakdown_template", []):
                if row.program == program_name and row.academic_year == acadyear:
                    fee_breakdown = row
                    break
            
            if fee_breakdown and students.custom_student_category == "Day Student" and fee_breakdown.day_student_fee:
                context.fee_pdf_url = fee_breakdown.day_student_fee
                context.has_fee_breakdown = True
            elif fee_breakdown and students.custom_student_category == "Boarder" and fee_breakdown.boarders_fee:
                context.fee_pdf_url = fee_breakdown.boarders_fee
                context.has_fee_breakdown = True
            elif fee_breakdown and fee_breakdown.day_student_fee and not students.custom_student_category:
                context.fee_pdf_url = fee_breakdown.day_student_fee
                context.has_fee_breakdown = True
            else:
                context.fee_pdf_url = None
                context.has_fee_breakdown = False
                
        except Exception as e:
            frappe.log_error(f"Error fetching fee breakdown: {str(e)}")
            context.fee_pdf_url = None
            context.has_fee_breakdown = False
    else:
        context.program = _("Welcome")
        context.fee_pdf_url = None
        context.has_fee_breakdown = False

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

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
            <td class="text-xs">{ledger.posting_date}</td>
            <td class="text-center"><a class="btn btn-link text-xs" href="/printview?doctype={ledger.voucher_type}&name={ledger.voucher_no}" target="_blank">{ledger.voucher_no}</a></td>
            <td class="text-xs">{ledger.voucher_type}</td>
            <td class="text-xs">{frappe.format_value(debit, {"fieldtype": "Currency"})}</td>
            <td class="text-xs">{frappe.format_value(credit, {"fieldtype": "Currency"})}</td>
            <td class="text-xs">{frappe.format_value(balance, {"fieldtype": "Currency"})}</td>
            <td class="text-xs">{ledger.remarks}</td>
        </tr>
        '''

    context.tbody_content = tbody_content
    context.total_debit = total_debit
    context.total_credit = total_credit
    context.balance = balance
    
    return context