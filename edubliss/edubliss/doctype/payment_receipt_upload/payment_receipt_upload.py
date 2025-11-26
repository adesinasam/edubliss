# Copyright (c) 2025, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, flt

class PaymentReceiptUpload(Document):
    def validate(self):
        self.validate_billing_documents()
        self.validate_allocated_amounts()
        self.validate_references()
        self.validate_multi_company_setup()
    
    def validate_billing_documents(self):
        """Validate billing documents and fetch relevant data"""
        for row in self.get("billing_receipts", []):
            if row.billing_document and row.billing_document_type:
                self.fetch_details_from_billing_doc(row)
    
    def fetch_details_from_billing_doc(self, row):
        """Fetch details from the linked billing document"""
        if row.billing_document_type == "Sales Invoice":
            # Use db_get to get fresh data from database
            sales_invoice_data = frappe.db.get_value(
                "Sales Invoice", 
                row.billing_document, 
                ["student", "posting_date", "outstanding_amount", "grand_total", "customer", "status", "company"],
                as_dict=True
            )
            
            if sales_invoice_data:
                row.student = sales_invoice_data.student
                row.posting_date = sales_invoice_data.posting_date
                row.outstanding = sales_invoice_data.outstanding_amount
                row.grand_total = sales_invoice_data.grand_total
                
                # Check if Sales Invoice is valid for payment
                if sales_invoice_data.status == "Cancelled":
                    frappe.throw(_("Sales Invoice {0} is cancelled and cannot be used for payment").format(row.billing_document))
        
    def validate_allocated_amounts(self):
        """Validate that allocated amounts don't exceed outstanding amounts"""
        total_allocated = 0
        for row in self.billing_receipts:
            total_allocated += flt(row.allocated_amount)
            
            # Get current outstanding amount with fresh database query
            if row.billing_document_type == "Sales Invoice" and row.billing_document:
                current_outstanding = frappe.db.get_value(
                    "Sales Invoice", 
                    row.billing_document, 
                    "outstanding_amount"
                )
                
                if not current_outstanding:
                    frappe.throw(_("Sales Invoice {0} not found").format(row.billing_document))
                
                if flt(row.allocated_amount) > flt(current_outstanding):
                    frappe.throw(_(
                        "Allocated amount {0} for {1} {2} cannot be greater than outstanding amount {3}"
                    ).format(
                        row.allocated_amount,
                        row.billing_document_type,
                        row.billing_document,
                        current_outstanding
                    ))
        
        # Validate total allocated equals paid amount
        if abs(total_allocated - flt(self.paid_amount)) > 0.01:
            frappe.throw(_(
                "Total allocated amount ({0}) must equal paid amount ({1})"
            ).format(total_allocated, self.paid_amount))
    
    def validate_references(self):
        """Validate reference_no and reference_date for bank transactions"""
        if self.mode_of_payment:
            mode_of_payment_type = frappe.db.get_value(
                "Mode of Payment", 
                self.mode_of_payment, 
                "type"
            )
            
            if mode_of_payment_type == "Bank":
                if not self.attach_image:
                    frappe.throw(_(
                        "Please attach either an image for bank transactions"
                    ))
                if not self.reference_no or not self.reference_date:
                    frappe.throw(_(
                        "Cheque/Reference No or Cheque/Reference Date cannot be empty"
                    ))
    
    def validate_multi_company_setup(self):
        """Validate that Mode of Payment is configured for all companies used in billing receipts"""
        if not self.mode_of_payment:
            return
            
        companies_in_receipts = set()
        
        for row in self.billing_receipts:
            if row.billing_document_type == "Sales Invoice" and row.billing_document:
                company = frappe.db.get_value("Sales Invoice", row.billing_document, "company")
                if company:
                    companies_in_receipts.add(company)
        
        # Check if Mode of Payment has accounts for all companies
        for company in companies_in_receipts:
            mode_of_payment_account = frappe.get_value(
                "Mode of Payment Account",
                {
                    "parent": self.mode_of_payment,
                    "company": company
                },
                "default_account"
            )
            
            if not mode_of_payment_account:
                frappe.throw(_(
                    "Mode of Payment '{0}' is not configured for company '{1}'. "
                    "Please set up Mode of Payment Account for this company in Mode of Payment settings."
                ).format(self.mode_of_payment, company))
    
    def on_submit(self):
        """Create and submit Payment Entry on submit"""
        self.validate_references()
        self.create_payment_entries()
        self.db_set('status', 'Approved')
    
    def on_cancel(self):
        """Handle cancellation"""
        # Find all Payment Entries created from this Payment Receipt Upload
        payment_entries = frappe.get_all(
            "Payment Entry",
            filters={
                "reference_no": self.name,
                "docstatus": 1  # Submitted
            },
            pluck="name"
        )

        for pe_name in payment_entries:
            try:
                pe = frappe.get_doc("Payment Entry", pe_name)
                pe.cancel()
                frappe.msgprint(_("Payment Entry {0} has been cancelled").format(pe_name))
            except Exception as e:
                frappe.log_error(f"Error cancelling Payment Entry {pe_name}: {str(e)}")
                frappe.throw(_("Failed to cancel Payment Entry {0}: {1}").format(pe_name, str(e)))

        self.db_set('status', 'Cancelled')
    
    def create_payment_entries(self):
        """Create Payment Entry for each billing receipt, handling multi-company"""
        successful_payments = []
        skipped_invoices = []
        failed_invoices = []
        
        for row in self.billing_receipts:
            if row.billing_document_type == "Sales Invoice":
                try:
                    # Get company from Sales Invoice
                    company = frappe.db.get_value("Sales Invoice", row.billing_document, "company")
                    
                    if not company:
                        failed_invoices.append({
                            'invoice': row.billing_document,
                            'error': _("Could not determine company")
                        })
                        continue
                    
                    # Validate that Mode of Payment has account for this company
                    mode_of_payment_account = frappe.get_value(
                        "Mode of Payment Account",
                        {
                            "parent": self.mode_of_payment,
                            "company": company
                        },
                        "default_account"
                    )
                    
                    if not mode_of_payment_account:
                        failed_invoices.append({
                            'invoice': row.billing_document,
                            'error': _("Mode of Payment not configured for company {0}").format(company)
                        })
                        continue
                    
                    # Check current outstanding with database lock to prevent race conditions
                    frappe.db.commit()  # Ensure fresh connection
                    
                    current_outstanding = frappe.db.sql("""
                        SELECT outstanding_amount 
                        FROM `tabSales Invoice` 
                        WHERE name = %s 
                        FOR UPDATE
                    """, (row.billing_document,), as_dict=True)
                    
                    if not current_outstanding or flt(current_outstanding[0].outstanding_amount) <= 0:
                        skipped_invoices.append(row.billing_document)
                        frappe.msgprint(_(
                            "Skipping Sales Invoice {0} - already fully paid. Outstanding: {1}"
                        ).format(row.billing_document, 
                                current_outstanding[0].outstanding_amount if current_outstanding else 0), 
                            indicator="orange")
                        continue
                    
                    # Validate allocated amount doesn't exceed current outstanding
                    if flt(row.allocated_amount) > flt(current_outstanding[0].outstanding_amount):
                        failed_invoices.append({
                            'invoice': row.billing_document,
                            'error': _("Allocated amount exceeds current outstanding amount")
                        })
                        continue
                    
                    # Create payment entry
                    payment_entry = self.create_payment_entry_for_sales_invoice(row, company)
                    successful_payments.append({
                        'payment_entry': payment_entry.name,
                        'sales_invoice': row.billing_document,
                        'company': company
                    })
                    
                except Exception as e:
                    error_message = str(e)
                    frappe.log_error(
                        title=f"Error creating Payment Entry for {row.billing_document}",
                        message=f"Payment Receipt Upload: {self.name}\nCompany: {company}\nError: {error_message}"
                    )
                    
                    if "has already been fully paid" in error_message:
                        skipped_invoices.append(row.billing_document)
                        frappe.msgprint(_(
                            "Sales Invoice {0} was already paid by another process"
                        ).format(row.billing_document), indicator="orange")
                    else:
                        failed_invoices.append({
                            'invoice': row.billing_document,
                            'error': error_message
                        })

    def create_payment_entry_for_sales_invoice(self, row, company):
        """Create Payment Entry for Sales Invoice reference with proper company context"""
        try:
            # Get Sales Invoice details with fresh data
            frappe.db.commit()
            si_data = frappe.db.get_value(
                "Sales Invoice",
                row.billing_document,
                ["customer", "customer_name", "debit_to", "outstanding_amount", "grand_total", "status"],
                as_dict=True
            )
            
            if not si_data:
                frappe.throw(_("Sales Invoice {0} not found").format(row.billing_document))
            
            if si_data.status == "Cancelled":
                frappe.throw(_("Sales Invoice {0} is cancelled").format(row.billing_document))
            
            # Create Payment Entry
            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = si_data.customer
            payment_entry.party_name = si_data.customer_name
            payment_entry.posting_date = self.posting_date or getdate(nowdate())
            payment_entry.company = company  # Use company from Sales Invoice
            payment_entry.mode_of_payment = self.mode_of_payment
            payment_entry.paid_amount = flt(row.allocated_amount)
            payment_entry.received_amount = flt(row.allocated_amount)
            payment_entry.custom_payment_receipt_upload = self.name
            payment_entry.reference_no = self.reference_no
            payment_entry.reference_date = self.reference_date or getdate(nowdate())
            payment_entry.remarks = f"Payment against Sales Invoice {row.billing_document} via Payment Receipt Upload {self.name}"
            
            # Set paid from account (customer account) - belongs to the same company as Sales Invoice
            payment_entry.paid_from = si_data.debit_to
            
            # Set paid to account from mode of payment for the specific company
            mode_of_payment_account = frappe.get_value(
                "Mode of Payment Account",
                {
                    "parent": self.mode_of_payment,
                    "company": company
                },
                "default_account"
            )
            
            if not mode_of_payment_account:
                frappe.throw(_(
                    "No default account found for Mode of Payment {0} in company {1}"
                ).format(self.mode_of_payment, company))
            
            payment_entry.paid_to = mode_of_payment_account
            
            # Get current outstanding amount with lock
            current_outstanding = frappe.db.sql("""
                SELECT outstanding_amount 
                FROM `tabSales Invoice` 
                WHERE name = %s
            """, (row.billing_document,), as_dict=True)[0].outstanding_amount
            
            # Add reference to Sales Invoice
            payment_entry.append("references", {
                "reference_doctype": "Sales Invoice",
                "reference_name": row.billing_document,
                "total_amount": si_data.grand_total,
                "outstanding_amount": current_outstanding,
                "allocated_amount": flt(row.allocated_amount)
            })
            
            # Insert and submit Payment Entry
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_(
                "Payment Entry {0} created and submitted for Sales Invoice {1} in company {2}"
            ).format(payment_entry.name, row.billing_document, company))
            
            return payment_entry
            
        except Exception as e:
            frappe.log_error(
                title=f"Error in create_payment_entry_for_sales_invoice for {row.billing_document}",
                message=f"Company: {company}\nPayment Receipt Upload: {self.name}\nError: {str(e)}"
            )
            raise