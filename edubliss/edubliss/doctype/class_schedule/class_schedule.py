# Copyright (c) 2025, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, time, timedelta

class ClassSchedule(Document):
    def validate(self):
        self.validate_student_group_unique()
        self.validate_subject_schedule_conflicts()

    def validate_student_group_unique(self):
        """Ensure student_group is not duplicated in submitted ClassSchedule"""
        if not self.student_group:
            return

        existing = frappe.db.exists(
            "Class Schedule",
            {
                "student_group": self.student_group,
                "docstatus": 1,  # submitted
                "name": ["!=", self.name],  # exclude self
            },
        )
        if existing:
            frappe.throw(
                f"Student Group <b>{self.student_group}</b> already has a submitted Class Schedule ({existing})."
            )

    def after_insert(self):
        # When a new ClassSchedule is created, reset is_cancelled=0 for all its Subject Schedules
        frappe.db.set_value(
            "Subject Schedule",
            {"parent": self.name, "parenttype": "Class Schedule"},
            "is_cancelled",
            0,
        )

    def on_submit(self):
        # Same as after_insert, ensure on submission children are active
        frappe.db.set_value(
            "Subject Schedule",
            {"parent": self.name, "parenttype": "Class Schedule"},
            "is_cancelled",
            0,
        )

    def on_cancel(self):
        # When ClassSchedule is cancelled, set is_cancelled=1 for all children
        frappe.db.set_value(
            "Subject Schedule",
            {"parent": self.name, "parenttype": "Class Schedule"},
            "is_cancelled",
            1,
        )

    def validate_subject_schedule_conflicts(self):
        seen = set()

        for row in self.subject_schedule:
            from_time = normalize_time(row.from_time)
            to_time = normalize_time(row.to_time)

            key_course = (row.week_days, row.from_time, row.to_time, row.course)
            key_instructor = (row.week_days, row.from_time, row.to_time, row.instructor)

            # 1. Validate inside the same document
            if key_course in seen:
                frappe.throw(f"Course {row.course} already scheduled on {row.week_days} "
                             f"from {row.from_time} to {row.to_time}.")
            if key_instructor in seen:
                frappe.throw(f"Instructor {row.instructor} already scheduled on {row.week_days} "
                             f"from {row.from_time} to {row.to_time}.")

            seen.add(key_course)
            seen.add(key_instructor)

            # 2. Validate against database (other ClassSchedules)
            overlaps = frappe.get_all(
                "Subject Schedule",
                filters={
                    "week_days": row.week_days,
                    "is_cancelled": 0,
                    "name": ["!=", row.name],  # exclude itself
                },
                fields=["name", "from_time", "to_time", "course", "instructor", "parent"],
            )

            for ss in overlaps:
                ss_from = normalize_time(ss.from_time)
                ss_to = normalize_time(ss.to_time)

                # check time overlap
                if (from_time < ss_to) and (to_time > ss_from):
                    if row.instructor == ss.instructor:
                        frappe.throw(
                            f"Instructor {row.instructor} already scheduled in ClassSchedule {ss.parent} "
                            f"on {row.week_days} from {ss.from_time} to {ss.to_time}."
                        )

            overlapss = frappe.get_all(
                "Subject Schedule",
                filters={
                    "student_group": row.student_group,
                    "week_days": row.week_days,
                    "is_cancelled": 0,
                    "name": ["!=", row.name],  # exclude itself
                },
                fields=["name", "student_group", "from_time", "to_time", "course", "instructor", "parent"],
            )

            for tt in overlapss:
                tt_from = normalize_time(tt.from_time)
                tt_to = normalize_time(tt.to_time)

                # check time overlap
                if (from_time < tt_to) and (to_time > tt_from):
                    if row.course == tt.course:
                        frappe.throw(
                            f"Course {row.course} already scheduled in ClassSchedule {tt.parent} "
                            f"on {row.week_days} from {tt.from_time} to {tt.to_time}."
                        )


def normalize_time(val):
    """Convert DB or form value to datetime.time"""
    if isinstance(val, str):
        return datetime.strptime(val, "%H:%M:%S").time()
    if isinstance(val, datetime):
        return val.time()
    if isinstance(val, timedelta):
        return (datetime.min + val).time()
    if isinstance(val, time):
        return val
    return None

