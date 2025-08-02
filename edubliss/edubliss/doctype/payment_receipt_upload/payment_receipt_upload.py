# Copyright (c) 2025, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentReceiptUpload(Document):
    def validate(self):
        self.validate_billing_documents()
    
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
    
    # def on_submit(self):
    #     self.update_outstanding_amounts()
    
    # def update_outstanding_amounts(self):
    #     """Update outstanding amounts in linked documents"""
    #     for row in self.get("billing_receipts", []):
    #         if row.billing_document and row.billing_document_type == "Sales Invoice":
    #             frappe.db.set_value(
    #                 "Sales Invoice", 
    #                 row.billing_document, 
    #                 "outstanding_amount", 
    #                 row.outstanding - row.allocated_amount
    #             )