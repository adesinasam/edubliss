import frappe
from frappe import _

def on_update(student, method):
    if not student.guardians or not student.customer:
        return

    add_guardian_to_customer_portal(student)

def add_guardian_to_customer_portal(student):
    try:
        customer_doc = frappe.get_doc("Customer", student.customer)
    except:
        return

    added_users = []

    for guardian in student.guardians:
        try:
            guardian_doc = frappe.get_doc("Guardian", guardian.guardian)
            if not guardian_doc.email_address:
                continue

            # Check/Create User
            user_name = (
                frappe.db.get_value("User", guardian_doc.email_address, "name")
                or create_user(guardian_doc)
            )
            if not user_name:
                continue

            # Skip if already in portal
            if user_name in [d.user for d in customer_doc.portal_users or []]:
                continue

            # Add to portal
            customer_doc.append("portal_users", {"user": user_name})
            added_users.append(user_name)
        except:
            continue

    if added_users:
        customer_doc.save(ignore_permissions=True)
        frappe.db.commit()

def create_user(guardian_doc):
    try:
        user = frappe.get_doc({
            "doctype": "User",
            "email": guardian_doc.email_address,
            "first_name": guardian_doc.guardian_name,
            "send_welcome_email": 0,
            "role_profile_name": "MPIS Parent",
            "user_type": "Website User"
        }).insert(ignore_permissions=True)
        return user.name
    except:
        return None