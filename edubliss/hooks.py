app_name = "edubliss"
app_title = "Edubliss"
app_publisher = "Adesina"
app_description = "School Portal and Dashboard Extension"
app_email = "support@glistercp.com.ng"
app_license = "mit"

# Apps
# ------------------

required_apps = ["education","lms"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
  {
    "name": "edubliss",
    "logo": "/assets/edubliss/dist/media/logo.png",
    "title": "Edubliss",
    "route": "/edubliss"
    # "has_permission": "edubliss.api.permission.has_app_permission"
  }
]

# Includes in <head>
# ------------------
fixtures = [{
  'dt' : 'Custom Field', 'filters':[
    [
      'name', 'in', [
        'Student-custom_prev_school',
        'Student-custom_tab_7',
        'Student-custom_school',
        'Course-custom_disabled',
        'Course-custom_subject',
        'Course-custom_course_category',
        'Course-custom_course_code',
        'Program-custom_school',
        'Program Course-custom_type',
        'Program Enrollment-custom_school',
        'Item-custom_fee_component_type',
        'Sales Invoice Item-custom_fee_component_type',
        'Assessment Result Tool-custom_course',
        'Assessment Result Tool-custom_assessment_group'
      ]
    ]
  ]
}]

# include js, css files in header of desk.html
# app_include_css = "/assets/edubliss/css/edubliss.css"
# app_include_js = "/assets/edubliss/js/edubliss.js"

# include js, css files in header of web template
# web_include_css = "/assets/edubliss/css/styles.css"
# web_include_js = "/assets/edubliss/dist/js/layouts/demo1.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "edubliss/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
doctype_js = {
    "Assessment Plan": "public/js/pages/assessment_plan.js",
    "Assessment Result": "public/js/pages/assessment_result.js",
    "Assessment Result Tool": "public/js/pages/assessment_result_tool.js",
    "LMS Batch": "public/js/pages/lms_batch.js",
    "Program": "public/js/pages/program.js",
    "Course Scheduling Tool": "public/js/pages/course_scheduling_tool.js",
    "Fee Structure": "public/js/pages/fee_structure.js",
    "Quotation": "public/js/pages/quotation.js",
    "Sales Order": "public/js/pages/sorder.js",
    "Sales Invoice": "public/js/pages/sinvoice.js",
    "Lead": "public/js/pages/lead.js",
    "Program Enrollment": "public/js/pages/program_enrollment.js",
    "Program Enrollment Tool": "public/js/pages/program_enrollment_tool.js",
    "Student": "public/js/pages/student.js"
    }

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "edubliss/public/icons.svg"

# Home Pages
# ----------
# application home page (will override Website Settings)
home_page = "portal"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

website_route_rules = [
    {"from_route": "/", "to_route": "portal"},
    {"from_route": "/index", "to_route": "portal"},
    {"from_route": "/edubliss", "to_route": "dashboard"},
    {"from_route": "/dashboard/index", "to_route": "dashboard"},
    {"from_route": "/students/profile/<docname>", "to_route": "students/profile"},
    {"from_route": "/students/family/<docname>", "to_route": "students/family"},
    {"from_route": "/students/billing/<docname>", "to_route": "students/billing"},
    {"from_route": "/students/enrollment/<docname>", "to_route": "students/enrollment"},
    {"from_route": "/students/gradebook/<docname>", "to_route": "students/gradebook"},
    {"from_route": "/students/gradebook_details/<docname>", "to_route": "students/gradebook_details"},
    {"from_route": "/students/progress_report/<docname>", "to_route": "students/progress_report"},
    {"from_route": "/students/report_card/<docname>", "to_route": "students/report_card"},
    {"from_route": "/students/lms/<docname>", "to_route": "students/lms"},
    {"from_route": "/students/schedule/<docname>", "to_route": "students/schedule"},
    {"from_route": "/students/timetable/<docname>", "to_route": "students/timetable"},
    {"from_route": "/students/ledger/<docname>", "to_route": "students/ledger"},
    {"from_route": "/students/fee/<docname>", "to_route": "students/fee"},
    {"from_route": "/students/attendance/<docname>", "to_route": "students/attendance"},
    {"from_route": "/teachers/profile/<docname>", "to_route": "teachers/profile"},
    {"from_route": "/teachers/course/<docname>", "to_route": "teachers/course"},
    {"from_route": "/teachers/schedule/<docname>", "to_route": "teachers/schedule"},
    {"from_route": "/teachers/timetable/<docname>", "to_route": "teachers/timetable"},
    {"from_route": "/teachers/sections/<docname>", "to_route": "teachers/sections"},
    {"from_route": "/parents/profile/<docname>", "to_route": "parents/profile"},
    {"from_route": "/parents/billing/<docname>", "to_route": "parents/billing"},
    {"from_route": "/parents/receipt_upload/<docname>", "to_route": "parents/receipt_upload"},
    {"from_route": "/admin/course/overview/<docname>", "to_route": "admin/course/overview"},
    {"from_route": "/admin/course/students/<docname>", "to_route": "admin/course/students"},
    {"from_route": "/admin/course/outline/<docname>", "to_route": "admin/course/outline"},
    {"from_route": "/admin/course/assessment/<docname>", "to_route": "admin/course/assessment"},
    {"from_route": "/admin/course/assessment_plan/<docname>", "to_route": "admin/course/assessment_plan"},
    {"from_route": "/admin/course/gradebook/<docname>", "to_route": "admin/course/gradebook"},
    {"from_route": "/admin/course/schedule/<docname>", "to_route": "admin/course/schedule"},
    {"from_route": "/admin/program/gradebook/<docname>", "to_route": "admin/program/gradebook"},
    {"from_route": "/admin/program/assessment_plan/<docname>", "to_route": "admin/program/assessment_plan"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "edubliss.utils.jinja_methods",
# 	"filters": "edubliss.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "edubliss.install.before_install"
# after_install = "edubliss.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "edubliss.uninstall.before_uninstall"
# after_uninstall = "edubliss.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "edubliss.utils.before_app_install"
# after_app_install = "edubliss.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "edubliss.utils.before_app_uninstall"
# after_app_uninstall = "edubliss.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "edubliss.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
  "Assessment Plan": {
    # "on_update": "edubliss.edubliss.assessment_plan.get_instructors",
    "on_submit": "edubliss.edubliss.assessment_plan.get_instructors",
    "on_cancel": "edubliss.edubliss.assessment_plan.setup"
  },
  "Program Enrollment": {
    "on_update": "edubliss.edubliss.program_enrollment.on_update_after_save",
    "on_submit": "edubliss.edubliss.program_enrollment.setup"
  },
  "Payment Entry": {
    "on_submit": "edubliss.edubliss.payment_entry.send_email_to_party"
  },
  "Course": {
    "validate": "edubliss.edubliss.course.validate"
  },
  "Student": {
    "on_update": "edubliss.edubliss.student.on_update"
  },
  "Lead": {
    "on_update": "edubliss.edubliss.lead.on_update_after_save"
  }
}
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"edubliss.tasks.all"
# 	],
# 	"daily": [
# 		"edubliss.tasks.daily"
# 	],
# 	"hourly": [
# 		"edubliss.tasks.hourly"
# 	],
# 	"weekly": [
# 		"edubliss.tasks.weekly"
# 	],
# 	"monthly": [
# 		"edubliss.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "edubliss.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "edubliss.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "edubliss.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["edubliss.utils.before_request"]
# after_request = ["edubliss.utils.after_request"]

# Job Events
# ----------
# before_job = ["edubliss.utils.before_job"]
# after_job = ["edubliss.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"edubliss.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

