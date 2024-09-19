import frappe
from frappe import _
from frappe import utils
from frappe.utils import cstr, flt, getdate, nowdate
from frappe import _, msgprint
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.query_builder.functions import Min
from frappe.utils import comma_and, get_link_to_form, getdate

@frappe.whitelist()
def get_courses(program):
    return frappe.db.sql(
        """select name from `tabLMS Course` where custom_program = %s and published = 1""",
        (program),
        as_dict=1,
    )

@frappe.whitelist()
def get_users_for_student_group(doctype, txt, searchfield, start, page_len, filters):
    # Get the student group from the filters
    student_group = filters.get("student_group")
    
    # Fetch students from the selected Student Group
    students = frappe.get_all("Student Group Student", filters={"parent": student_group}, fields=["student"])
    student_ids = [student.student for student in students]
    
    # Fetch user_ids from the Student doctype
    user_ids = frappe.get_all("Student", filters={"name": ["in", student_ids]}, fields=["user"])

    # Return the user_ids in the format required by Frappe's query function (name and label)
    return [[user.user, user.user] for user in user_ids]

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_program_courses(doctype, txt, searchfield, start, page_len, filters):
    if not filters.get("program"):
        frappe.msgprint(_("Please select a Program first."))
        return []

    doctype = "LMS Course"
    return frappe.db.sql(
        """select name, title from `tabLMS Course`
        where  custom_program = %(program)s and name like %(txt)s {match_cond}
        order by
            if(locate(%(_txt)s, name), locate(%(_txt)s, course), 99999),
            `tabLMS Course`.name asc
        limit {start}, {page_len}""".format(
            match_cond=get_match_cond(doctype), start=start, page_len=page_len
        ),
        {
            "txt": "%{0}%".format(txt),
            "_txt": txt.replace("%", ""),
            "program": filters["program"],
        },
    )
