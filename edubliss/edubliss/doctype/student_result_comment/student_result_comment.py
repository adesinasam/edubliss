# Copyright (c) 2024, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from frappe.utils.csvutils import getlink


class StudentResultComment(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		comment_result = frappe.get_list(
			"Student Result Comment",
			filters={
				"name": ("not in", [self.name]),
				"student": self.student,
				"student_group": self.student_group,
				"comment_type": self.comment_type,
				"docstatus": ("!=", 2),
			},
		)
		if comment_result:
			frappe.throw(
				_("Student Result Comment record {0} already exists.").format(
					getlink("Student Result Comment", comment_result[0].name)
				)
			)
