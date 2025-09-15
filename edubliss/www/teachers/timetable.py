import frappe
from frappe import _

no_cache = 1

def get_teachers():
    instructors = frappe.qb.DocType("Instructor")
    employees = frappe.qb.DocType("Employee")

    instructors_query = (
        frappe.qb.from_(employees)
        .inner_join(instructors)
        .on(instructors.employee == employees.name)
        .select('*')
        .where(employees.user_id == frappe.session.user)
        .run(as_dict=1)
    )
    return instructors_query if instructors_query else []

def get_context(context):

    docnames = frappe.form_dict.docname

    if docnames:
        docname = docnames
    else:
        teacher = get_teachers()
        if teacher:
            docname = teacher[0].name
        else:
            docname = None

    # login
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    # Fetch the current user's details
    current_user = frappe.get_doc("User", frappe.session.user)
    context.current_user = current_user

    # Fetch the roles of the current user
    user_roles = frappe.get_roles(frappe.session.user)
    context.user_roles = user_roles

    # Split the company name into parts
    parts = current_user.full_name.split(" ")

    # Create the abbreviation by taking the first letter of each part
    context.abbr = "".join([p[0] for p in parts[:2] if p])

    # nav
    context.active_route = "teachers"
    context.active_subroute = "teacher_list"
    context.active_teacher_route = "schedule"

    context.docname = docname

    edubliss_session = frappe.call('edubliss.api.get_edubliss_user_session')
    if edubliss_session:
        context.edublisession = edubliss_session
        company = edubliss_session.school
        acadyear = edubliss_session.academic_year
        acadterm = edubliss_session.academic_term
    else:
        context.edublisession = _("Welcome")  # Assuming welcome is a placeholder message
        company = None
        acadyear = None
        acadterm = None

    context.company = company
    context.acadyear = acadyear
    context.acadterm = acadterm

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')
    # context.teachers = frappe.call('edubliss.api.get_teachers')

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        context.teachers = frappe.get_doc("Instructor", docname)
        staff = context.teachers
    except frappe.DoesNotExistError:
        frappe.throw(_("Teacher not found"), frappe.DoesNotExistError)

    if staff:
        try:
            context.employees = frappe.get_doc("Employee", staff.employee)
        except frappe.DoesNotExistError:
            frappe.throw(_("Employee Record not found"), frappe.DoesNotExistError)

        try:
            subject_schedules = frappe.call(
                'edubliss.api.get_instructor_subject_schedules', 
                instructor=docname, 
                academic_term=acadterm
                )
        except Exception as e:
            subject_schedules = None  # or set a default value if required        

        if subject_schedules:

            try:
                schedules = frappe.call(
                    'edubliss.api.get_instructor_class_schedule',
                    instructor=docname,
                    academic_term=acadterm
                    )
            except Exception as e:
                schedules = None  # or set a default value if required        

            if schedules:
                schedule = frappe.get_doc("Class Schedule", schedules)
                context.schedules = schedule.name
                context.schedule_name = schedules
                timetable_slots = frappe.call('edubliss.api.get_timetable_slots', schedule=schedules)

                # Normalize subject_schedules and timetable_slots to lists of dicts
                subject_schedules = subject_schedules or []
                timetable_slots = timetable_slots or []

                # Build a quick lookup: for each week_day -> { period_label : subject_row }
                # Note: subject_schedules entries returned by get_all should already be dict-like.
                schedule_lookup = {}
                for s in subject_schedules:
                    # expected keys: week_days (Link), period_label (Link name), course, instructor, room, is_cancelled, instructor_name ...
                    day = s.get("week_days") or s.get("week_day") or "Unknown"
                    period = s.get("period_label") or s.get("period_label_name") or None
                    if not day or not period:
                        continue
                    schedule_lookup.setdefault(day, {})[period] = s

                # Determine the list/order of days to display.
                # Use distinct week_days from subject_schedules, or fallback to a reasonable order.
                days_order = []

                # Get all active days from Week Days, ordered by list_no
                all_days = frappe.get_all(
                    "Week Days",
                    filters={"disabled": 0},
                    fields=["week_days"],
                    order_by="list_no asc",
                    pluck="week_days"
                )

                # Collect only the days that actually appear in subject_schedules
                seen = set(s.get("week_days") for s in subject_schedules if s.get("week_days"))

                # Keep the order defined in Week Days (list_no), but filter to only used days
                days_order = [d for d in all_days if d in seen]

                # If no subject_schedules days exist, fall back to all ordered days
                if not days_order:
                    days_order = all_days

                # # keep insertion order from subject_schedules
                # seen = set()
                # for s in subject_schedules:
                #     d = s.get("week_days")
                #     if d and d not in seen:
                #         days_order.append(d)
                #         seen.add(d)

                # # If no days found from subject_schedules, maybe use common week list
                # if not days_order:
                #     days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

                # Prepare timetable_map: for each day, create a list matching timetable_slots order
                timetable_map = {}
                for day in days_order:
                    row = []
                    for slot in timetable_slots:
                        period_label_name = slot.get("period_label") or slot.get("period_label_name") or slot.get("name")
                        cell = schedule_lookup.get(day, {}).get(period_label_name)
                        # We may want to enrich the cell (e.g. fetch instructor name or course name display)
                        if cell:
                            # ensure instructor_name present if fetched by link
                            if "instructor" in cell and not cell.get("instructor_name"):
                                # attempt to fetch instructor name quickly (optional)
                                try:
                                    instr_doc = frappe.get_cached_doc("Instructor", cell["instructor"])
                                    cell["instructor_name"] = getattr(instr_doc, "instructor_name", None)
                                except Exception:
                                    pass
                            # compute course_name for display
                            if "course" in cell and not cell.get("course_name"):
                                try:
                                    course_doc = frappe.get_cached_doc("Course", cell["course"])
                                    cell["course_name"] = getattr(course_doc, "custom_subject", cell["course"])
                                except Exception:
                                    cell["course_name"] = cell.get("course")
                        row.append(cell)
                    timetable_map[day] = row

                # push context for the template
                context.subject_schedules = subject_schedules
                context.timetable_slots = timetable_slots
                context.timetable_map = timetable_map
                context.days_order = days_order


    return context
