import frappe
from frappe import _
from datetime import datetime

no_cache = 1

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
        .orderby(assessment_criteria.custom_order_name)
        .run(as_dict=1)
    )
    return assessment_result_criteria_query if assessment_result_criteria_query else []

def get_structure_marks(assessment_result_name,assessment_plan):
    assessment_result_structure = frappe.qb.DocType("Assessment Result Structure")
    assessment_result = frappe.qb.DocType("Assessment Result")
    assessment_plan_structure = frappe.qb.DocType("Assessment Plan Structure")

    assessment_result_structure_query = (
        frappe.qb.from_(assessment_result_structure)
        .inner_join(assessment_result).on(assessment_result_structure.parent == assessment_result.name)
        .inner_join(assessment_plan_structure).on(assessment_result_structure.assessment_type == assessment_plan_structure.assessment_type)
        .select(assessment_result.name,assessment_result.assessment_plan,assessment_result_structure.assessment_type, 
            assessment_result_structure.score, assessment_result_structure.grade, assessment_plan_structure.topics)
        .where(assessment_result_structure.parent == assessment_result_name)
        .where(assessment_result.name == assessment_result_name)
        .where(assessment_plan_structure.parent == assessment_plan)
        .orderby(assessment_plan_structure.topics)
        .run(as_dict=1)
    )
    return assessment_result_structure_query if assessment_result_structure_query else []

def get_marks_avg(course,program,academic_term):
    assessment_results = frappe.get_all('Assessment Result',
        filters={'course': course, 'program': program, 'academic_term': academic_term, 'grading_scale': 'MPIS Grade Scale', 'docstatus': ("!=", 2)}, 
        fields=[
            'name', 'academic_term', 'student_group', 'course', 'grading_scale',
            'maximum_score', 'total_score', 'grade'
        ], 
        order_by="")

    total_score = 0
    course_count = 0
    for result in assessment_results:
        score = result.total_score
        total_score += score
        course_count += 1  # Increment by 1 for each course
    average = total_score / course_count if course_count else 0  # Avoid division by zero
    return average

def get_grade(grading_scale,score):
    return frappe.call('edubliss.api.get_grade', grading_scale=grading_scale, percentage=score)

def get_grade_remark(grading_scale,score):
    percentages = ((score / 100) * 100)
    return frappe.call('edubliss.api.get_grade_remark', grading_scale=grading_scale, percentage=percentages)

def get_grade_comment(grading_scale,grade):
    grades = frappe.qb.DocType("Grading Scale")
    grades_interval = frappe.qb.DocType("Grading Scale Interval")

    grades_interval_query = (
        frappe.qb.from_(grades)
        .inner_join(grades_interval)
        .on(grades.name == grades_interval.parent)
        .select(grades_interval.grade_description)
        .where(grades.name == grading_scale)
        .where(grades_interval.parent == grading_scale)
        .where(grades_interval.grade_code == grade)
        .run(as_dict=1)
    )
    return grades_interval_query[0]['grade_description'] if grades_interval_query else None

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

def get_context(context):

    docnames = frappe.form_dict.docname

    if docnames:
        docname = docnames
    else:
        student = frappe.get_list("Student", filters={"student_email_id": frappe.session.user}, limit_page_length=1)
        if student:
            docname = student[0].name
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
    context.active_route = "students"
    context.active_subroute = "student_list"
    context.active_student_route = "progress_report"

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
        acadterm = None  # Set acadterm to None to avoid potential errors if no session exists

    context.company = edubliss_session.school
    context.acadyear = edubliss_session.academic_year
    context.acadterm = edubliss_session.academic_term

    context.companys = frappe.call('edubliss.api.get_company')
    context.acadyears = frappe.call('edubliss.api.get_academic_year')
    context.acadterms = frappe.call('edubliss.api.get_academic_term')

    # Try to fetch the Student document and handle errors if it doesn't exist
    try:
        students = frappe.get_doc("Student", docname)
        context.students = students
        customer = students.customer
    except frappe.DoesNotExistError:
        frappe.throw(_("Student not found"), frappe.DoesNotExistError)

    try:
        context.acad_terms = frappe.get_doc("Academic Term", acadterm)
    except frappe.DoesNotExistError:
        frappe.throw(_("Academic Term not found"), frappe.DoesNotExistError)

    # Try to fetch the Student Program Enrollment document and handle errors if it doesn't exist
    try:
        program = frappe.call(
            'edubliss.api.get_student_program',
            student=docname, 
            academic_year=acadyear, 
            academic_term=acadterm
        )
    except Exception as e:
        program = ''  # or set a default value if required        

    if program:
        context.program = program
        program_enrollment = context.program.name   
        program_name = context.program.program
        context.programs = frappe.get_doc("Program", program_name)
        context.program_courses = frappe.call('edubliss.api.get_program_courses', program=program_name)

        # Try to fetch the Student Group document and handle errors if it doesn't exist
        try:
            sections = frappe.call(
                'edubliss.api.get_student_groups', 
                student=docname, 
                program=program_name, 
                academic_term=acadterm
                )
        except Exception as e:
            sections = None  # or set a default value if required        

        if sections:
            section = frappe.get_doc("Student Group", sections)
            context.section = section
            context.sections_name = sections

        # Try to fetch the Student Courses document and handle errors if it doesn't exist
        try:
            courses = frappe.call(
                'edubliss.api.get_student_courses',
                student=docname, 
                program_enrollment=program_enrollment
                )
        except Exception as e:
            courses = None  # or set a default value if required        

        if courses:
            context.courses = courses    

        context.term = frappe.get_doc("Academic Term", acadterm)
        context.assessment_criteria = frappe.get_all('Assessment Criteria',
            filters={'assessment_criteria_group': "PERFORMANCE IN SUBJECTS"}, 
            fields=['custom_abbr', 'assessment_criteria_group', 'assessment_criteria', 'custom_order_name', 'weightage'], 
            order_by="custom_order_name asc")
    
        assessment_results = frappe.get_all('Assessment Result',
            filters={
            'student': docname,
            'program': program_name, 
            'academic_year': acadyear, 
            'academic_term': acadterm,
            'docstatus': ("!=", 2)
            }, 
            fields=[
                'name', 'student', 'program', 'academic_year', 'academic_term', 'student_group', 
                'course', 'assessment_plan', 'student_name', 'assessment_group', 'grading_scale',
                'maximum_score', 'total_score', 'grade', 'comment'
            ], 
            order_by="")

        if assessment_results:
            context.assessment_result = assessment_results
            context.section_count = len(section.get("students"))
            context.instructor = section.get("instructors")
            context.program_count = len(frappe.get_all('Program Enrollment',
                filters={
                'program': program_name, 
                'academic_year': acadyear, 
                'academic_term': acadterm,
                'docstatus': 1
                }, 
                order_by=""))

            total_score = 0
            course_count = 0
            for result in assessment_results:
                if get_course_subject(result.course) != 'Others':
                    scale = result.grading_scale
                    score = result.total_score
                    total_score += score
                    course_count += 1  # Increment by 1 for each course
            context.total_score = total_score
            context.course_count = course_count
            context.average = total_score / course_count if course_count else 0  # Avoid division by zero
            grading_scale = scale

            grading_scales = frappe.get_doc("Grading Scale", grading_scale)
            context.grading_scales = grading_scales
            context.grading_scale_intervals = grading_scales.get("intervals")

            all_results = frappe.get_all(
                'Assessment Result',
                filters={
                'program': program_name,
                'academic_year': acadyear,
                'academic_term': acadterm,
                'docstatus': ("!=", 2)
                },
                fields=['student', 'total_score', 'course']
                )

            # Calculate total and average scores for each student
            student_scores = {}
            for result in all_results:
                if get_course_subject(result.course) != 'Others':
                    student = result.student
                    scores = result.total_score
                    if student not in student_scores:
                        student_scores[student] = {'total_score': 0, 'course_count': 0}
                    student_scores[student]['total_score'] += scores
                    student_scores[student]['course_count'] += 1

            # Calculate average score for each student
            for student, data in student_scores.items():
                data['average'] = data['total_score'] / data['course_count']

            # Sort students by their average scores in descending order
            sorted_students = sorted(student_scores.items(), key=lambda x: x[1]['average'], reverse=True)

            # Find the target student's position
            target_student = docname
            context.class_position = next((i + 1 for i, (student, _) in enumerate(sorted_students) if student == target_student), None)

            section_results = frappe.get_all(
                'Assessment Result',
                filters={
                'program': program_name,
                'student_group': sections,
                'academic_year': acadyear,
                'academic_term': acadterm,
                'docstatus': ("!=", 2)
                },
                fields=['student', 'total_score', 'course']
                )

            # Calculate total and average scores for each student
            student_scores = {}
            for result in section_results:
                if get_course_subject(result.course) != 'Others':
                    student = result.student
                    scores = result.total_score
                    if student not in student_scores:
                        student_scores[student] = {'total_score': 0, 'course_count': 0}
                    student_scores[student]['total_score'] += scores
                    student_scores[student]['course_count'] += 1

            # Calculate average score for each student
            for student, data in student_scores.items():
                data['average'] = data['total_score'] / data['course_count']

            # Sort students by their average scores in descending order
            sorted_studentss = sorted(student_scores.items(), key=lambda x: x[1]['average'], reverse=True)

            # Find the target student's position
            target_students = docname
            context.sections_position = next((i + 1 for i, (student, _) in enumerate(sorted_studentss) if student == target_students), None)

            # get the attendance of the student for that peroid of time.
            context.attendance = get_attendance_count(
                docname, acadterm
            )

            context['format_date'] = format_date
            context['get_course_subject'] = get_course_subject
            context['get_criteria_marks'] = get_criteria_marks
            context['get_grade'] = get_grade
            context['get_grade_remark'] = get_grade_remark
            context['get_grade_comment'] = get_grade_comment
            context['get_course_teacher'] = get_course_teacher
            context['get_marks_avg'] = get_marks_avg
            context['get_structure_marks'] = get_structure_marks

            try:
                comment_results = frappe.get_all(
                    'Student Result Comment',
                    filters={
                    'student': docname,
                    'student_group': sections,
                    'academic_year': acadyear,
                    'academic_term': acadterm,
                    'docstatus': ("!=", 2)
                    },
                    fields=['*']
                    )
            except Exception as e:
                comment_results=None

            if comment_results:
                for comment in comment_results:
                    if comment.comment_type=='HEAD TEACHER':
                        context.comment_result_head = comment.name
                        context.comment_result_head_instructor = comment.teacher
                        context.comment_result_head_comment = comment.comment
                        context.comment_result_head_sign = comment.signature
                        context.comment_result_head_img = comment.signature_image
                        context.comment_result_head_upload = comment.upload_signature
                    else:
                        context.comment_result = comment.name
                        context.comment_result_instructor = comment.teacher
                        context.comment_result_comment = comment.comment
                        context.comment_result_sign = comment.signature
                        context.comment_result_img = comment.signature_image
                        context.comment_result_upload = comment.upload_signature

    else:
        context.program = _("Welcome")  # or set a default value if required


    return context