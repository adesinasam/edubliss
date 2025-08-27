import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Sum
from frappe.utils import flt, nowdate
from frappe.utils.background_jobs import enqueue

from erpnext import get_company_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
	get_payment_entry,
)
from erpnext.accounts.doctype.subscription_plan.subscription_plan import get_plan_rate
from erpnext.accounts.party import get_party_account, get_party_bank_account
from erpnext.accounts.utils import get_account_currency, get_currency_precision
from erpnext.utilities import payment_app_import_guard

ALLOWED_DOCTYPES_FOR_PAYMENT_REQUEST = [
	"Sales Order",
	"Purchase Order",
	"Sales Invoice",
	"Purchase Invoice",
	"POS Invoice",
	"Fees",
]


@frappe.whitelist(allow_guest=True)
def make_payment_request(**args):
	"""Make payment request"""

	args = frappe._dict(args)

	if args.dt not in ALLOWED_DOCTYPES_FOR_PAYMENT_REQUEST:
		frappe.throw(_("Payment Requests cannot be created against: {0}").format(frappe.bold(args.dt)))

	ref_doc = frappe.get_doc(args.dt, args.dn)
	company_name = ref_doc.get("company")

	if company_name:
		gateway_account = get_company_gateway_details(company_name)
	else:
		gateway_account = get_gateway_details(args) or frappe._dict()

	partial_amount = args.amt
	student_id = args.studentid

	# Retrieve the Comapny Default Bank Account
	payment_account = frappe.db.get_value('Company', ref_doc.get("company"), 'default_bank_account')

	if partial_amount:
		grand_total = partial_amount
	else:
		grand_total = get_amount(ref_doc, payment_account)
		# grand_total = get_amount(ref_doc, gateway_account.get("payment_account"))

	if not grand_total:
		frappe.throw(_("Payment Entry is already created"))
	if args.loyalty_points and args.dt == "Sales Order":
		from erpnext.accounts.doctype.loyalty_program.loyalty_program import validate_loyalty_points

		loyalty_amount = validate_loyalty_points(ref_doc, int(args.loyalty_points))
		frappe.db.set_value(
			"Sales Order", args.dn, "loyalty_points", int(args.loyalty_points), update_modified=False
		)
		frappe.db.set_value("Sales Order", args.dn, "loyalty_amount", loyalty_amount, update_modified=False)
		grand_total = grand_total - loyalty_amount

	# fetches existing payment request `grand_total` amount
	existing_payment_request_amount = get_existing_payment_request_amount(ref_doc)

	def validate_and_calculate_grand_total(grand_total, existing_payment_request_amount):
		grand_total -= existing_payment_request_amount
		if not grand_total:
			frappe.throw(_("Payment Request is already created"))
		return grand_total

	if existing_payment_request_amount:
		if args.order_type == "Shopping Cart":
			# If Payment Request is in an advanced stage, then create for remaining amount.
			if get_existing_payment_request_amount(
				ref_doc, ["Initiated", "Partially Paid", "Payment Ordered", "Paid"]
			):
				grand_total = validate_and_calculate_grand_total(grand_total, existing_payment_request_amount)
			else:
				# If PR's are processed, cancel all of them.
				cancel_old_payment_requests(ref_doc.doctype, ref_doc.name)
		else:
			grand_total = validate_and_calculate_grand_total(grand_total, existing_payment_request_amount)

	draft_payment_request = frappe.db.get_value(
		"Payment Request",
		{"reference_doctype": ref_doc.doctype, "reference_name": ref_doc.name, "docstatus": 0},
	)

	if draft_payment_request:
		frappe.db.set_value(
			"Payment Request", draft_payment_request, "grand_total", grand_total, update_modified=False
		)
		pr = frappe.get_doc("Payment Request", draft_payment_request)
	else:
		bank_account = (
			get_party_bank_account(args.get("party_type"), args.get("party"))
			if args.get("party_type")
			else ""
		)
		pr = frappe.new_doc("Payment Request")

		if not args.get("payment_request_type"):
			args["payment_request_type"] = (
				"Outward" if args.get("dt") in ["Purchase Order", "Purchase Invoice"] else "Inward"
			)

		party_type = args.get("party_type") or "Customer"
		party_account_currency = ref_doc.get("party_account_currency")

		if not party_account_currency:
			party_account = get_party_account(party_type, ref_doc.get(party_type.lower()), ref_doc.company)
			party_account_currency = get_account_currency(party_account)

		pr.update(
			{
				"payment_gateway_account": gateway_account.get("name"),
				"payment_gateway": gateway_account.get("payment_gateway"),
				# "payment_account": gateway_account.get("payment_account"),
				"payment_account": payment_account,
				"payment_channel": gateway_account.get("payment_channel"),
				"payment_request_type": args.get("payment_request_type"),
				"currency": ref_doc.currency,
				"party_account_currency": party_account_currency,
				"grand_total": grand_total,
				"mode_of_payment": args.mode_of_payment,
				"email_to": frappe.session.user,
				"subject": _("Payment Request for {0}").format(args.dn),
				"message": gateway_account.get("message") or get_dummy_message(ref_doc),
				"reference_doctype": args.dt,
				"reference_name": args.dn,
				"company": ref_doc.get("company"),
				"party_type": party_type,
				"party": args.get("party") or ref_doc.get("customer"),
				"bank_account": bank_account,
				"party_name": args.get("party_name") or ref_doc.get("customer_name"),
				"phone_number": args.get("phone_number") if args.get("phone_number") else None,
				"custom_redirect": _("/students/billing/{0}").format(student_id),
			}
		)

		# Update dimensions
		pr.update(
			{
				"cost_center": ref_doc.get("cost_center"),
				"project": ref_doc.get("project"),
			}
		)

		for dimension in get_accounting_dimensions():
			pr.update({dimension: ref_doc.get(dimension)})

		if args.order_type == "Shopping Cart" or args.mute_email:
			pr.flags.mute_email = True

		if frappe.db.get_single_value("Accounts Settings", "create_pr_in_draft_status", cache=True):
			pr.insert(ignore_permissions=True)
		if args.submit_doc:
			if pr.get("__unsaved"):
				pr.insert(ignore_permissions=True)
			pr.submit()

	if args.order_type == "Shopping Cart":
		frappe.db.commit()
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = pr.get_payment_url()

	if args.return_doc:
		return pr

	return pr.as_dict()


def get_amount(ref_doc, payment_account=None):
	"""get amount based on doctype"""
	grand_total = 0

	dt = ref_doc.doctype
	if dt in ["Sales Order", "Purchase Order"]:
		advance_amount = flt(ref_doc.advance_paid)
		if ref_doc.party_account_currency != ref_doc.currency:
			advance_amount = flt(flt(ref_doc.advance_paid) / ref_doc.conversion_rate)

		grand_total = (flt(ref_doc.rounded_total) or flt(ref_doc.grand_total)) - advance_amount

	elif dt in ["Sales Invoice", "Purchase Invoice"]:
		if (
			dt == "Sales Invoice"
			and ref_doc.is_pos
			and ref_doc.payments
			and any(
				[
					payment.type == "Phone" and payment.account == payment_account
					for payment in ref_doc.payments
				]
			)
		):
			grand_total = sum(
				[
					payment.amount
					for payment in ref_doc.payments
					if payment.type == "Phone" and payment.account == payment_account
				]
			)
		else:
			if ref_doc.party_account_currency == ref_doc.currency:
				grand_total = flt(ref_doc.outstanding_amount)
			else:
				grand_total = flt(flt(ref_doc.outstanding_amount) / ref_doc.conversion_rate)
	elif dt == "POS Invoice":
		for pay in ref_doc.payments:
			if pay.type == "Phone" and pay.account == payment_account:
				grand_total = pay.amount
				break
	elif dt == "Fees":
		grand_total = ref_doc.outstanding_amount

	return flt(grand_total, get_currency_precision()) if grand_total > 0 else 0


def get_irequest_status(payment_requests: None | list = None) -> list:
	IR = frappe.qb.DocType("Integration Request")
	res = []
	if payment_requests:
		res = (
			frappe.qb.from_(IR)
			.select(IR.name)
			.where(IR.reference_doctype.eq("Payment Request"))
			.where(IR.reference_docname.isin(payment_requests))
			.where(IR.status.isin(["Authorized", "Completed"]))
			.run(as_dict=True)
		)
	return res


def cancel_old_payment_requests(ref_dt, ref_dn):
	PR = frappe.qb.DocType("Payment Request")

	if res := (
		frappe.qb.from_(PR)
		.select(PR.name)
		.where(PR.reference_doctype == ref_dt)
		.where(PR.reference_name == ref_dn)
		.where(PR.docstatus == 1)
		.where(PR.status.isin(["Draft", "Requested"]))
		.run(as_dict=True)
	):
		if get_irequest_status([x.name for x in res]):
			frappe.throw(_("Another Payment Request is already processed"))
		else:
			for x in res:
				# doc = frappe.get_doc("Payment Request", x.name)
				# doc.flags.ignore_permissions = True
				# doc.cancel()
				frappe.db.set_value("Payment Request", x.name, {"docstatus": 2, "status": "Cancelled" }, update_modified=False)

				# if ireqs := get_irequests_of_payment_request(doc.name):
				# 	for ireq in ireqs:
				# 		frappe.db.set_value("Integration Request", ireq.name, "status", "Cancelled")


def get_existing_payment_request_amount(ref_doc, statuses: list | None = None) -> list:
	"""
	Return the total amount of Payment Requests against a reference document.
	"""
	PR = frappe.qb.DocType("Payment Request")

	query = (
		frappe.qb.from_(PR)
		.select(Sum(PR.outstanding_amount))
		.where(PR.reference_doctype == ref_doc.doctype)
		.where(PR.reference_name == ref_doc.name)
		.where(PR.docstatus == 1)
	)

	if statuses:
		query = query.where(PR.status.isin(statuses))

	response = query.run()

	os_amount_in_transaction_currency = flt(response[0][0] if response[0] else 0)

	if ref_doc.currency != ref_doc.party_account_currency:
		os_amount_in_transaction_currency = flt(os_amount_in_transaction_currency / ref_doc.conversion_rate)

	return os_amount_in_transaction_currency


def get_company_gateway_details(company_name):
	"""
	Return gateway and payment account of company payment gateway
	"""

	# Try to get gateway account for the specific company
	gateway_account = get_payment_gateway_account({"company": company_name})

	if gateway_account:
		return gateway_account

	# Fall back to default gateway account
	return get_payment_gateway_account({"is_default": 1})


def get_gateway_details(args):  # nosemgrep
	"""
	Return gateway and payment account of default payment gateway
	"""
	gateway_account = args.get("payment_gateway_account", {"is_default": 1})
	if gateway_account:
		return get_payment_gateway_account(gateway_account)

	gateway_account = get_payment_gateway_account({"is_default": 1})

	return gateway_account


def get_payment_gateway_account(args):
	return frappe.db.get_value(
		"Payment Gateway Account",
		args,
		["name", "payment_gateway", "payment_account", "message"],
		as_dict=1,
	)


@frappe.whitelist()
def get_print_format_list(ref_doctype):
	print_format_list = ["Standard"]

	print_format_list.extend(
		[p.name for p in frappe.get_all("Print Format", filters={"doc_type": ref_doctype})]
	)

	return {"print_format": print_format_list}


@frappe.whitelist(allow_guest=True)
def resend_payment_email(docname):
	return frappe.get_doc("Payment Request", docname).send_email()


@frappe.whitelist()
def make_payment_entry(docname):
	doc = frappe.get_doc("Payment Request", docname)
	return doc.create_payment_entry(submit=False).as_dict()


def update_payment_requests_as_per_pe_references(references=None, cancel=False):
	"""
	Update Payment Request's `Status` and `Outstanding Amount` based on Payment Entry Reference's `Allocated Amount`.
	"""
	if not references:
		return

	precision = references[0].precision("allocated_amount")

	referenced_payment_requests = frappe.get_all(
		"Payment Request",
		filters={"name": ["in", {row.payment_request for row in references if row.payment_request}]},
		fields=[
			"name",
			"grand_total",
			"outstanding_amount",
			"payment_request_type",
		],
	)

	referenced_payment_requests = {pr.name: pr for pr in referenced_payment_requests}

	for ref in references:
		if not ref.payment_request:
			continue

		payment_request = referenced_payment_requests[ref.payment_request]
		pr_outstanding = payment_request["outstanding_amount"]

		# update outstanding amount
		new_outstanding_amount = flt(
			pr_outstanding + ref.allocated_amount if cancel else pr_outstanding - ref.allocated_amount,
			precision,
		)

		# to handle same payment request for the multiple allocations
		payment_request["outstanding_amount"] = new_outstanding_amount

		if not cancel and new_outstanding_amount < 0:
			frappe.throw(
				msg=_(
					"The allocated amount is greater than the outstanding amount of Payment Request {0}"
				).format(ref.payment_request),
				title=_("Invalid Allocated Amount"),
			)

		# update status
		if new_outstanding_amount == payment_request["grand_total"]:
			status = "Initiated" if payment_request["payment_request_type"] == "Outward" else "Requested"
		elif new_outstanding_amount == 0:
			status = "Paid"
		elif new_outstanding_amount > 0:
			status = "Partially Paid"

		# update database
		frappe.db.set_value(
			"Payment Request",
			ref.payment_request,
			{"outstanding_amount": new_outstanding_amount, "status": status},
		)


def get_dummy_message(doc):
	return frappe.render_template(
		"""{% if doc.contact_person -%}
<p>Dear {{ doc.contact_person }},</p>
{%- else %}<p>Hello,</p>{% endif %}

<p>{{ _("Requesting payment against {0} {1} for amount {2}").format(doc.doctype,
	doc.name, doc.get_formatted("grand_total")) }}</p>

<a href="{{ payment_url }}">{{ _("Make Payment") }}</a>

<p>{{ _("If you have any questions, please get back to us.") }}</p>

<p>{{ _("Thank you for your business!") }}</p>
""",
		dict(doc=doc, payment_url="{{ payment_url }}"),
	)


@frappe.whitelist()
def get_subscription_details(reference_doctype, reference_name):
	if reference_doctype == "Sales Invoice":
		subscriptions = frappe.db.sql(
			"""SELECT parent as sub_name FROM `tabSubscription Invoice` WHERE invoice=%s""",
			reference_name,
			as_dict=1,
		)
		subscription_plans = []
		for subscription in subscriptions:
			plans = frappe.get_doc("Subscription", subscription.sub_name).plans
			for plan in plans:
				subscription_plans.append(plan)
		return subscription_plans


@frappe.whitelist()
def make_payment_order(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc

	def set_missing_values(source, target):
		target.payment_order_type = "Payment Request"
		target.append(
			"references",
			{
				"reference_doctype": source.reference_doctype,
				"reference_name": source.reference_name,
				"amount": source.grand_total,
				"supplier": source.party,
				"payment_request": source_name,
				"mode_of_payment": source.mode_of_payment,
				"bank_account": source.bank_account,
				"account": source.account,
			},
		)

	doclist = get_mapped_doc(
		"Payment Request",
		source_name,
		{
			"Payment Request": {
				"doctype": "Payment Order",
			}
		},
		target_doc,
		set_missing_values,
	)

	return doclist


def validate_payment(doc, method=None):
	if doc.reference_doctype != "Payment Request" or (
		frappe.db.get_value(doc.reference_doctype, doc.reference_docname, "status") != "Paid"
	):
		return

	frappe.throw(
		_("The Payment Request {0} is already paid, cannot process payment twice").format(
			doc.reference_docname
		)
	)


@frappe.whitelist()
def get_open_payment_requests_query(doctype, txt, searchfield, start, page_len, filters):
	# permission checks in `get_list()`
	filters = frappe._dict(filters)

	if not filters.reference_doctype or not filters.reference_name:
		return []

	if txt:
		filters.name = ["like", f"%{txt}%"]

	open_payment_requests = frappe.get_list(
		"Payment Request",
		filters=filters,
		fields=["name", "grand_total", "outstanding_amount"],
		order_by="transaction_date ASC,creation ASC",
	)

	return [
		(
			pr.name,
			_("<strong>Grand Total:</strong> {0}").format(pr.grand_total),
			_("<strong>Outstanding Amount:</strong> {0}").format(pr.outstanding_amount),
		)
		for pr in open_payment_requests
	]


def get_irequests_of_payment_request(doc: str | None = None) -> list:
	res = []
	if doc:
		res = frappe.db.get_all(
			"Integration Request",
			{
				"reference_doctype": "Payment Request",
				"reference_docname": doc,
				"status": "Queued",
			},
		)
	return res
