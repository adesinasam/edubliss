import frappe
from frappe import _


def validate(course, method):
    if course.assessment_structure:
        total_weightage = 0
        for structure in course.assessment_structure:
            total_weightage += structure.weightage or 0
        if total_weightage != 100:
            frappe.throw(_("Total Weightage of all Assessment Structure must be 100%"))
