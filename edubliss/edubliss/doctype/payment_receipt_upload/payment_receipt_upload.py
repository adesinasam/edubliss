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
        
        successful_payments = []
        skipped_invoices = []
        
        for row in self.billing_receipts:
            if row.billing_document_type == "Sales Invoice":
                try:
                    # Check current outstanding before creating payment
                    current_outstanding = frappe.db.get_value(
                        "Sales Invoice", 
                        row.billing_document, 
                        "outstanding_amount"
                    )
                    
                    if flt(current_outstanding) <= 0:
                        skipped_invoices.append(row.billing_document)
                        frappe.msgprint(_(
                            "Skipping Sales Invoice {0} - already fully paid. Outstanding: {1}"
                        ).format(row.billing_document, current_outstanding), indicator="orange")
                        continue
                    
                    # Create payment entry using Frappe's built-in function
                    payment_entry = self.create_payment_entry_for_sales_invoice(row, company)
                    successful_payments.append({
                        'payment_entry': payment_entry.name,
                        'sales_invoice': row.billing_document
                    })
                    
                except Exception as e:
                    frappe.log_error(f"Error creating Payment Entry for {row.billing_document}: {str(e)}")
                    if "has already been fully paid" in str(e):
                        skipped_invoices.append(row.billing_document)
                        frappe.msgprint(_(
                            "Sales Invoice {0} was already paid by another process"
                        ).format(row.billing_document), indicator="orange")
                    else:
                        frappe.throw(_(
                            "Failed to create Payment Entry for Sales Invoice {0}: {1}"
                        ).format(row.billing_document, str(e)))
        
        # Show summary
        if successful_payments:
            frappe.msgprint(_("Successfully created {0} Payment Entries").format(len(successful_payments)))
        
        if skipped_invoices:
            frappe.msgprint(_("Skipped {0} already paid invoices").format(len(skipped_invoices)), indicator="orange")
    
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
        
        # Use the first company found
        company = mode_of_payment_accounts[0].company
        return company
    
    def create_payment_entry_for_sales_invoice(self, row, company):
        """Create Payment Entry for Sales Invoice reference using Frappe's built-in function"""
        try:
            # Use Frappe's built-in get_payment_entry function
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            
            # Get payment entry template from Sales Invoice
            payment_entry = get_payment_entry("Sales Invoice", row.billing_document)
            
            # Update with our specific details
            payment_entry.posting_date = self.posting_date or getdate(nowdate())
            payment_entry.company = company
            payment_entry.mode_of_payment = self.mode_of_payment
            payment_entry.reference_no = self.name
            payment_entry.reference_date = self.posting_date or getdate(nowdate())
            payment_entry.remarks = f"Payment via Payment Receipt Upload {self.name}"
            
            # Set the allocated amount specifically
            allocated_amount = flt(row.allocated_amount)
            for reference in payment_entry.references:
                reference.allocated_amount = allocated_amount
            
            # Update paid amounts based on allocated amount
            payment_entry.paid_amount = allocated_amount
            payment_entry.received_amount = allocated_amount
            payment_entry.base_paid_amount = allocated_amount
            payment_entry.base_received_amount = allocated_amount
            
            # Validate the payment entry before inserting
            payment_entry.validate()
            
            # Insert and submit
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_(
                "Payment Entry {0} created and submitted for Sales Invoice {1}"
            ).format(payment_entry.name, row.billing_document))
            
            return payment_entry
            
        except Exception as e:
            frappe.log_error(
                title=f"Error creating Payment Entry for {row.billing_document}",
                message=f"Payment Receipt Upload: {self.name}\nError: {str(e)}"
            )
            raise