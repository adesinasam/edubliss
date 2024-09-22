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
    # Get the student groups from the filters (handling multiple groups)
    student_groups = filters.get("student_group")
    excluded_users = filters.get("excluded_users", [])

    if not student_groups:
        return []

    # Ensure student_groups is a list (handle both single and multiple selections)
    if isinstance(student_groups, str):
        student_groups = [student_groups]

    # Fetch students from the selected Student Groups
    students = frappe.get_all(
        "Student Group Student", 
        filters={"parent": ["in", student_groups]}, 
        fields=["student"]
    )
    student_ids = [student.student for student in students]

    if not student_ids:
        return []

    # Fetch user_ids from the Student doctype
    user_ids = frappe.get_all(
        "Student", 
        filters={"name": ["in", student_ids]}, 
        fields=["user"]
    )

    # Exclude already selected user IDs
    user_ids = [user for user in user_ids if user.user not in excluded_users]

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
