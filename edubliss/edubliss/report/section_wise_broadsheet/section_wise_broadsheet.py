# Copyright (c) 2024, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def execute(filters=None):
    """Main entry point for the report."""
    data, courses = get_data(filters)
    columns = get_columns(courses)
    return columns, data

def get_columns(courses):
    """Define the columns for the report, dynamically adding courses."""
    columns = [
        {"fieldname": "student", "label": "Student ID", "fieldtype": "Link", "options": "Student", "width": 150},
        {"fieldname": "student_name", "label": "Student Name", "fieldtype": "Data", "width": 200},
    ]
    
    # Add a column for each course
    for course in courses:
        columns.append({
            "fieldname": f"course_{course.lower().replace(' ', '_')}",
            "label": course,
            "fieldtype": "Float",
            "width": 120
        })
    
    # Add total and average columns
    columns.extend([
        {"fieldname": "total_courses", "label": "Total Courses", "fieldtype": "Int", "width": 120},
        {"fieldname": "total_score", "label": "Total Score", "fieldtype": "Float", "width": 120},
        {"fieldname": "average_score", "label": "Average Score", "fieldtype": "Float", "width": 120},
        {"fieldname": "position", "label": "Position", "fieldtype": "Int", "width": 100},
    ])
    return columns

def get_data(filters=None):
    """Fetch the report data."""
    if not filters or not filters.get("student_group"):
        return [], []

    student_group = filters["student_group"]

    # Fetch students in the selected Student Group
    students = frappe.get_all(
        "Student Group Student",
        filters={"parent": student_group},
        fields=["student", "student_name"]
    )

    if not students:
        return [], []

    # Map to student ID for use in Assessment Result queries
    student_ids = [student.student for student in students]

    # Fetch assessment results grouped by Course and Student
    assessment_data = frappe.db.sql(
        """
        SELECT
            ar.student,
            ar.student_name,
            ar.course,
            SUM(ar.total_score) AS total_score
        FROM
            `tabAssessment Result` ar
        WHERE
            ar.student IN %(students)s
            AND ar.docstatus = 1
        GROUP BY
            ar.student, ar.course
        """,
        {"students": student_ids},
        as_dict=True
    )

    # Prepare data and extract unique courses
    courses = set()
    results = {}

    for row in assessment_data:
        student = row["student"]
        course = row["course"]

        # Collect unique courses
        courses.add(course)

        # Aggregate student data
        if student not in results:
            results[student] = {
                "student": row["student"],
                "student_name": row["student_name"],
                "total_score": 0,
                "course_count": 0,
                "courses": {}
            }

        results[student]["courses"][course] = flt(row["total_score"])
        results[student]["total_score"] += flt(row["total_score"])
        results[student]["course_count"] += 1

    # Rank students based on total score
    ranked_students = sorted(
        results.values(), key=lambda x: x["total_score"], reverse=True
    )

    # Format the results with position rankings
    formatted_results = []
    for position, student_data in enumerate(ranked_students, start=1):
        row = {
            "student": student_data["student"],
            "student_name": student_data["student_name"],
            "total_courses": student_data["course_count"],
            "total_score": student_data["total_score"],
            "average_score": student_data["total_score"] / (student_data["course_count"] or 1),
            "position": position
        }

        # Add course scores
        for course in courses:
            row[f"course_{course.lower().replace(' ', '_')}"] = student_data["courses"].get(course, 0)

        formatted_results.append(row)

    return formatted_results, sorted(courses)
