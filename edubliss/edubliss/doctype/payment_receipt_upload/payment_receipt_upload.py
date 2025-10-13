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
    
    def validate_billing_documents(self):
        """Validate billing documents and fetch relevant data"""
        for row in self.get("billing_receipts", []):
            if row.billing_document and row.billing_document_type:
                self.fetch_details_from_billing_doc(row)
    
    def fetch_details_from_billing_doc(self, row):
        """Fetch details from the linked billing document"""
        if row.billing_document_type == "Sales Invoice":
            sales_invoice = frappe.get_doc("Sales Invoice", row.billing_document)
            row.student = sales_invoice.student
            row.posting_date = sales_invoice.posting_date
            row.outstanding = sales_invoice.outstanding_amount
            row.grand_total = sales_invoice.base_grand_total
        # Add other document types as needed
        
    def validate_allocated_amounts(self):
        """Validate that allocated amounts don't exceed outstanding amounts"""
        total_allocated = 0
        for row in self.billing_receipts:
            total_allocated += flt(row.allocated_amount)
            
            # Get current outstanding amount
            if row.billing_document_type == "Sales Invoice" and row.billing_document:
                si_outstanding = frappe.db.get_value(
                    "Sales Invoice", 
                    row.billing_document, 
                    "outstanding_amount"
                )
                
                if flt(row.allocated_amount) > flt(si_outstanding):
                    frappe.throw(_(
                        "Allocated amount {0} for {1} {2} cannot be greater than outstanding amount {3}"
                    ).format(
                        row.allocated_amount,
                        row.billing_document_type,
                        row.billing_document,
                        si_outstanding
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
        """Create Payment Entry for each billing receipt"""
        company = self.get_company_for_mode_of_payment()
        
        for row in self.billing_receipts:
            if row.billing_document_type == "Sales Invoice":
                self.create_payment_entry_for_sales_invoice(row, company)
    
    def get_company_for_mode_of_payment(self):
        """Get company based on Mode of Payment settings"""
        if not self.mode_of_payment:
            frappe.throw(_("Mode of Payment is required"))
        
        # Get default company from Mode of Payment Account
        mode_of_payment_accounts = frappe.get_all(
            "Mode of Payment Account",
            filters={"parent": self.mode_of_payment},
            fields=["company", "default_account"]
        )
        
        if not mode_of_payment_accounts:
            frappe.throw(_(
                "No accounts configured for Mode of Payment {0}. Please set up Mode of Payment Account."
            ).format(self.mode_of_payment))
        
        # Use the first company found (you might want to enhance this logic based on your multi-company setup)
        company = mode_of_payment_accounts[0].company
        return company
    
    def create_payment_entry_for_sales_invoice(self, row, company):
        """Create Payment Entry for Sales Invoice reference"""
        try:
            # Get Sales Invoice details
            si = frappe.get_doc("Sales Invoice", row.billing_document)
            
            # Create Payment Entry
            payment_entry = frappe.new_doc("Payment Entry")
            payment_entry.payment_type = "Receive"
            payment_entry.party_type = "Customer"
            payment_entry.party = si.customer
            payment_entry.party_name = si.customer_name
            payment_entry.posting_date = self.posting_date or getdate(nowdate())
            payment_entry.company = company
            payment_entry.mode_of_payment = self.mode_of_payment
            payment_entry.paid_amount = flt(row.allocated_amount)
            payment_entry.received_amount = flt(row.allocated_amount)
            payment_entry.reference_no = self.name
            payment_entry.reference_date = self.posting_date or getdate(nowdate())
            payment_entry.remarks = f"Payment against Sales Invoice {row.billing_document} via Payment Receipt Upload {self.name}"
            
            # Set paid from account (customer account)
            payment_entry.paid_from = si.debit_to
            
            # Set paid to account from mode of payment
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
            
            # # Add reference to Sales Invoice
            # payment_entry.append("references", {
            #     "reference_doctype": "Sales Invoice",
            #     "reference_name": row.billing_document,
            #     "total_amount": si.grand_total,
            #     "outstanding_amount": si.outstanding_amount,
            #     "allocated_amount": flt(row.allocated_amount)
            # })
            
            # Insert and submit Payment Entry
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            # Add comment in Payment Receipt Upload
            frappe.msgprint(_(
                "Payment Entry {0} created and submitted for Sales Invoice {1}"
            ).format(payment_entry.name, row.billing_document))
            
        except Exception as e:
            frappe.log_error(f"Error creating Payment Entry for {row.billing_document}: {str(e)}")
            frappe.throw(_(
                "Failed to create Payment Entry for Sales Invoice {0}: {1}"
            ).format(row.billing_document, str(e)))