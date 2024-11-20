import frappe
from frappe import _
from frappe import utils
from frappe.utils import cstr, flt, getdate, nowdate

def setup(assessment_plan, method):

    if assessment_plan.docstatus == 2:         
        # Fetch all Empty Bottle Entry names matching the criteria
        pr_names = frappe.get_all("Assessment Result", 
            filters={"assessment_plan": assessment_plan.name, "docstatus": 0}, 
            fields=["name"]
        )
        # Iterate over each entry and update fields
        for entry in pr_names:
            pr_name = entry.name
            if pr_name:
                # Fetch the Empty Bottle Entry document using the retrieved name
                btl = frappe.get_doc('Assessment Result', pr_name)

                # Set the stock_entry_no field and the status to 'Cancelled'
                btl.db_set('docstatus', 2)  # Mark the document as cancelled


    # Return the initial program enrollment object
    return assessment_plan

def get_instructors(assessment_plan, method):

    instrutor = frappe.qb.DocType("Instructor")
    instrutor_course = frappe.qb.DocType("Instructor Log")

    instrutor_course_query = (
        frappe.qb.from_(instrutor)
        .inner_join(instrutor_course)
        .on(instrutor.name == instrutor_course.parent)
        .select(instrutor_course.parent)
        .where(instrutor_course.course == assessment_plan.course)
        .where(instrutor_course.academic_year == assessment_plan.academic_year)
        .where(instrutor_course.student_group == assessment_plan.student_group)
        .run(as_dict=1)
    )
    result = ", ".join(instructor['parent'] for instructor in instrutor_course_query) if instrutor_course_query else ""

    if result:
        btl = frappe.get_doc('Assessment Plan', assessment_plan.name)
        btl.db_set("custom_instructor", result)


    # Return the initial program enrollment object
    return assessment_plan
