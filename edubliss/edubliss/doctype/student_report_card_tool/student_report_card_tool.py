# Copyright (c) 2024, Adesina and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
from frappe.www.printview import get_letter_head
from datetime import datetime

from education.education.report.course_wise_assessment_report.course_wise_assessment_report import (
    get_child_assessment_groups, get_formatted_result)


class StudentReportCardTool(Document):
	pass

def format_date(value, format="%d/%m/%Y"):
    if value:
        return value.strftime(format)
    return value

def get_course_subject(course):
    course_doc = frappe.get_doc("Course", course)
    return course_doc.custom_subject

def get_course_teacher(course, student_group, academic_term):
    instructor = frappe.qb.DocType("Instructor")
    instructor_log = frappe.qb.DocType("Instructor Log")

    instructor_log_query = (
        frappe.qb.from_(instructor)
        .inner_join(instructor_log)
        .on(instructor.name == instructor_log.parent)
        .select(instructor_log.parent)
        .where(instructor_log.course == course)
        .where(instructor_log.student_group == student_group)
        .where(instructor_log.academic_term == academic_term)
        .where(instructor.status == 'Active')
        .run(as_dict=1)
    )
    instructor_details = instructor_log_query[0]['parent'] if instructor_log_query else None
    if instructor_details:
    	parts = instructor_details.split(" ")
    	# Capitalize the first word
    	first_word = parts[0].upper() if parts else ""
    	# Create the abbreviation by taking the first letter of the remaining words
    	abbreviation = " ".join([f"{p[0].upper()}." for p in parts[1:] if p])
    	return f"{first_word} {abbreviation}".strip()


def get_criteria_marks(assessment_result):
    assessment_result_criteria = frappe.qb.DocType("Assessment Result Detail")
    assessment_criteria = frappe.qb.DocType("Assessment Criteria")

    assessment_result_criteria_query = (
        frappe.qb.from_(assessment_result_criteria)
        .inner_join(assessment_criteria).on(assessment_result_criteria.assessment_criteria == assessment_criteria.assessment_criteria)
        .select('*')
        .where(assessment_result_criteria.parent == assessment_result)
        .where(assessment_criteria.assessment_criteria_group == "PERFORMANCE IN SUBJECTS")
        .orderby(assessment_criteria.custom_abbr)
        .run(as_dict=1)
    )
    return assessment_result_criteria_query if assessment_result_criteria_query else []

def get_grade_remark(grading_scale,score):
    percentages = ((score / 100) * 100)
    return frappe.call('edubliss.api.get_grade_remark', grading_scale=grading_scale, percentage=percentages)

@frappe.whitelist()
def preview_report_card(doc):
	doc = frappe._dict(json.loads(doc))
	doc.students = [doc.student]
	# values = get_formatted_result(doc, get_course=True)
	# courses = values.get("courses")
	# assessment_results = values.get("assessment_result")
	students = frappe.get_doc("Student", doc.students[0])
	program = frappe.get_doc("Program", doc.program)
	term = frappe.get_doc("Academic Term", doc.academic_term)
	assessment_criteria = frappe.get_all('Assessment Criteria',
		filters={'assessment_criteria_group': "PERFORMANCE IN SUBJECTS"}, 
		fields=['custom_abbr', 'assessment_criteria_group', 'assessment_criteria'], 
		order_by="custom_abbr asc")
	assessment_results = frappe.get_all('Assessment Result',
		filters={
		'student': doc.students[0],
		'program': doc.program, 
		'academic_year': doc.academic_year, 
		'academic_term': doc.academic_term,
		'docstatus': ("!=", 2)
		}, 
		fields=[
			'name', 'student', 'program', 'academic_year', 'academic_term', 'student_group', 
			'course', 'assessment_plan', 'student_name', 'assessment_group', 'grading_scale',
			'maximum_score', 'total_score', 'grade', 'comment'
		], 
		order_by="")

	sections = frappe.call(
		'edubliss.api.get_student_groups', 
		student=doc.students[0], 
		program=doc.program, 
		academic_year=doc.academic_year
		)
	section = frappe.get_doc("Student Group", sections)
	section_count = len(section.get("students"))
	instructor = section.get("instructors")
	program_count = len(frappe.get_all('Program Enrollment',
		filters={
		'program': doc.program, 
		'academic_year': doc.academic_year, 
		'academic_term': doc.academic_term,
		'docstatus': 1
		}, 
		order_by=""))
	# course_count = len(values.get("courses"))

	total_score = 0
	course_count = 0
	for result in assessment_results:
		score = result.total_score
		total_score += score
		course_count += 1  # Increment by 1 for each course
	average = total_score / course_count if course_count else 0  # Avoid division by zero

	# get the attendance of the student for that peroid of time.
	doc.attendance = get_attendance_count(
		doc.students[0], doc.academic_term
	)

	html = frappe.render_template(
		"edubliss/edubliss/doctype/student_report_card_tool/student_report_card_tool.html",
		{
			"doc": doc,
			"assessment_result": assessment_results,
			"assessment_criteria": assessment_criteria,
			"students": students,
			"program": program,
			"term": term,
			"sections": sections,
			"instructor": instructor,
			"course_count": course_count,
			"section_count": section_count,
			"program_count": program_count,
			"total_score": total_score,
			"average": average,
			"format_date": format_date,
			"get_course_subject": get_course_subject,
			"get_criteria_marks": get_criteria_marks,
			"get_grade_remark": get_grade_remark,
			"get_course_teacher": get_course_teacher,
		},
	)

	final_template = frappe.render_template(
		"frappe/www/printview.html", {"body": html, "title": "Report Card"}
	)

	frappe.response.filename = "Report Card " + doc.students[0] + ".pdf"
	frappe.response.filecontent = get_pdf(final_template)
	frappe.response.type = "pdf"


def get_attendance_count(student, academic_term):
	attendance = frappe._dict()
	attendance.total = 0

	from_date, to_date = frappe.db.get_value(
		"Academic Term", academic_term, ["term_start_date", "term_end_date"]
	)

	if from_date and to_date:
		data = frappe.get_all(
			"Student Attendance",
			{"student": student, "docstatus": 1, "date": ["between", (from_date, to_date)]},
			["status", "count(student) as count"],
			group_by="status",
		)

		for row in data:
			if row.status == "Present":
				attendance.present = row.count
			if row.status == "Absent":
				attendance.absent = row.count
			attendance.total += row.count
		return attendance
	else:
		frappe.throw(_("Please enter the Academic Term and set the Start and End date."))