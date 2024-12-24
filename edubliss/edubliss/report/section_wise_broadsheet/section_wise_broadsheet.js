// Copyright (c) 2024, Adesina and contributors
// For license information, please see license.txt

frappe.query_reports["Section-wise Broadsheet"] = {
    filters: [
        {
            fieldname: "student_group",
            label: __("Student Group"),
            fieldtype: "Link",
            options: "Student Group",
            reqd: 1
        },
        {
            fieldname: "program",
            label: __("Program"),
            fieldtype: "Link",
            options: "Program",
            read_only: 1
        },
        {
            fieldname: "academic_year",
            label: __("Academic Year"),
            fieldtype: "Link",
            options: "Academic Year",
            read_only: 1
        },
        {
            fieldname: "academic_term",
            label: __("Academic Term"),
            fieldtype: "Link",
            options: "Academic Term",
            read_only: 1
        }
    ],

    onload: function (report) {
        // Add "Back to Dashboard" button
        report.page.set_primary_action(
            `${frappe.utils.icon('arrow-left', 'sm')} ${__('Back to Dashboard')}`,
            function () {
                let student_group = frappe.query_report.get_filter_value("student_group");
                if (!student_group) {
                    frappe.msgprint(__("Please select a Student Group to proceed."));
                    return;
                }
                // Redirect to the desired URL
                window.location.href = `/admin/program/sections_details?section_name=${student_group}`;
            }
        );
    }
};
