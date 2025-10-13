# Copyright (c) 2025, Adesina and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class EdublissSettings(Document):
    def validate(self):
        self.validate_pdf_attachments()
    
    def validate_pdf_attachments(self):
        """Validate that all attachments are PDF files"""
        
        # Validate main form attachments
        self.validate_single_pdf_attachment('boarders_prospectus')
        self.validate_single_pdf_attachment('day_student_prospectus')
        
        # Validate table attachments
        if self.get('fee_breakdown_template'):
            for idx, row in enumerate(self.fee_breakdown_template):
                self.validate_table_pdf_attachment(row, 'day_student_fee', idx)
                self.validate_table_pdf_attachment(row, 'boarders_fee', idx)
    
    def validate_single_pdf_attachment(self, fieldname):
        """Validate PDF attachment for a single field"""
        if self.get(fieldname):
            if not self.is_pdf_file(self.get(fieldname)):
                frappe.throw(_(
                    "Field '{0}': Only PDF files are allowed. '{1}' is not a PDF file."
                ).format(
                    frappe.unscrub(fieldname),
                    self.get(fieldname)
                ))
    
    def validate_table_pdf_attachment(self, row, fieldname, row_idx):
        """Validate PDF attachment for table field"""
        if row.get(fieldname):
            if not self.is_pdf_file(row.get(fieldname)):
                frappe.throw(_(
                    "Row #{0}, Field '{1}': Only PDF files are allowed. '{2}' is not a PDF file."
                ).format(
                    row_idx + 1,
                    frappe.unscrub(fieldname),
                    row.get(fieldname)
                ))
    
    def is_pdf_file(self, file_url):
        """Check if the file is a PDF"""
        if not file_url:
            return True
            
        # Extract filename from URL
        filename = file_url.split('/')[-1]
        
        # Check if it's a PDF file
        return filename.lower().endswith('.pdf')