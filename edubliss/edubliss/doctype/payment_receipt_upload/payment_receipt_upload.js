// Copyright (c) 2025, Adesina and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Receipt Upload", {
    refresh(frm) {
        // Set user name if not set
        if (!frm.doc.user_name) {
            frm.set_value('user_name', frappe.session.user_fullname || frappe.session.user);
        }

        // Add custom button to show processing summary if document is submitted
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Show Processing Summary'), function() {
                frm.trigger('show_processing_summary');
            });
        }
    },

    setup(frm) {
        const me = this;
        
        // Set up query for billing document field
        frm.fields_dict.billing_receipts.grid.get_field("billing_document").get_query = function(doc, cdt, cdn) {
            const d = locals[cdt][cdn];
            const filters = [
                [d.billing_document_type, "docstatus", "=", "1"]
            ];

            // Additional filter for Purchase Invoices
            if (d.billing_document_type === "Sales Invoice") {
                filters.push(["Sales Invoice", "outstanding_amount", ">", "0"]);
            }

            return { filters: filters };
        };

        // Set up field mappings
        frm.add_fetch("billing_document", "student", "student");
        frm.add_fetch("billing_document", "posting_date", "posting_date");
        frm.add_fetch("billing_document", "outstanding_amount", "outstanding");
        frm.add_fetch("billing_document", "base_grand_total", "grand_total");
    },

    validate: function(frm) {
        // Validate that total allocated amount equals paid amount
        let total_allocated = 0;
        $.each(frm.doc.billing_receipts || [], function(i, row) {
            total_allocated += flt(row.allocated_amount);
        });

        if (Math.abs(total_allocated - flt(frm.doc.paid_amount)) > 0.01) {
            frappe.throw(__('Total allocated amount ({0}) must equal paid amount ({1})', [total_allocated, frm.doc.paid_amount]));
        }

        // Validate reference_no and reference_date if mode_of_payment requires it
        if (frm.doc.mode_of_payment) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Mode of Payment',
                    filters: { name: frm.doc.mode_of_payment },
                    fieldname: ['type']
                },
                callback: function(r) {
                    if (r.message && r.message.type === 'Bank') {
                        if (!frm.doc.attach_image) {
                            frappe.throw(__('Please attach either an image for bank transactions'));
                        }
                        if (!frm.doc.reference_no || !frm.doc.reference_date) {
                            frappe.throw(__('Cheque/Reference No or Cheque/Reference Date cannot be empty'));
                        }
                    }
                }
            });
        }
    },

    show_processing_summary: function(frm) {
        // Show loading indicator
        frm.dashboard.add_progress(__("Loading Processing Summary"), "Loading...");
        
        frappe.call({
            method: 'edubliss.edubliss.doctype.payment_receipt_upload.payment_receipt_upload.get_processing_summary',
            args: {
                payment_receipt_upload: frm.doc.name
            },
            callback: function(r) {
                frm.dashboard.hide_progress();
                
                if (r.message) {
                    const summary = r.message;
                    frm.trigger('display_processing_summary_dialog', summary);
                } else {
                    frappe.msgprint({
                        title: __('No Data'),
                        message: __('No processing summary data available for this document.'),
                        indicator: 'orange'
                    });
                }
            }
        });
    },

    display_processing_summary_dialog: function(frm, summary) {
        // Create a detailed dialog with processing summary
        const dialog = new frappe.ui.Dialog({
            title: __('Payment Processing Summary'),
            size: 'large',
            fields: [
                {
                    fieldname: 'summary_html',
                    fieldtype: 'HTML',
                    options: frm.trigger('generate_summary_html', summary)
                }
            ]
        });

        // Add refresh button
        dialog.set_primary_action(__('Refresh'), function() {
            dialog.hide();
            frm.trigger('show_processing_summary');
        });

        dialog.show();
    },

    generate_summary_html: function(frm, summary) {
        let html = `
            <div class="processing-summary">
                <style>
                    .processing-summary {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    }
                    .summary-section {
                        margin-bottom: 20px;
                        padding: 15px;
                        border-radius: 8px;
                        border-left: 4px solid #ccc;
                    }
                    .success-section {
                        background-color: #f0f9f0;
                        border-left-color: #28a745;
                    }
                    .warning-section {
                        background-color: #fffbf0;
                        border-left-color: #ffc107;
                    }
                    .error-section {
                        background-color: #fef0f0;
                        border-left-color: #dc3545;
                    }
                    .section-title {
                        font-weight: 600;
                        margin-bottom: 10px;
                        font-size: 14px;
                    }
                    .item-list {
                        margin: 0;
                        padding-left: 20px;
                    }
                    .item-list li {
                        margin-bottom: 5px;
                        font-size: 13px;
                    }
                    .stats-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                        margin-bottom: 20px;
                    }
                    .stat-card {
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                        background: white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .stat-number {
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }
                    .stat-label {
                        font-size: 12px;
                        color: #6c757d;
                    }
                    .success-stat { border-top: 4px solid #28a745; }
                    .warning-stat { border-top: 4px solid #ffc107; }
                    .error-stat { border-top: 4px solid #dc3545; }
                    .company-badge {
                        display: inline-block;
                        padding: 2px 8px;
                        background: #e9ecef;
                        border-radius: 12px;
                        font-size: 11px;
                        margin-left: 8px;
                    }
                </style>
        `;

        // Statistics Cards
        html += `
            <div class="stats-grid">
                <div class="stat-card success-stat">
                    <div class="stat-number" style="color: #28a745;">${summary.successful_count || 0}</div>
                    <div class="stat-label">Successful Payments</div>
                </div>
                <div class="stat-card warning-stat">
                    <div class="stat-number" style="color: #ffc107;">${summary.skipped_count || 0}</div>
                    <div class="stat-label">Skipped Invoices</div>
                </div>
                <div class="stat-card error-stat">
                    <div class="stat-number" style="color: #dc3545;">${summary.failed_count || 0}</div>
                    <div class="stat-label">Failed Invoices</div>
                </div>
            </div>
        `;

        // Successful Payments Section
        if (summary.successful_payments && summary.successful_payments.length > 0) {
            html += `
                <div class="summary-section success-section">
                    <div class="section-title">
                        ✅ ${__('Successful Payments')} (${summary.successful_payments.length})
                        ${summary.companies_count ? `<span class="company-badge">${summary.companies_count} companies</span>` : ''}
                    </div>
                    <ul class="item-list">
            `;
            
            summary.successful_payments.forEach(payment => {
                html += `
                    <li>
                        <strong>${payment.payment_entry}</strong> 
                        for ${payment.sales_invoice}
                        ${payment.company ? `<span class="company-badge">${payment.company}</span>` : ''}
                    </li>
                `;
            });
            
            html += `</ul></div>`;
        }

        // Skipped Invoices Section
        if (summary.skipped_invoices && summary.skipped_invoices.length > 0) {
            html += `
                <div class="summary-section warning-section">
                    <div class="section-title">
                        🟡 ${__('Skipped Invoices')} (${summary.skipped_invoices.length})
                    </div>
                    <ul class="item-list">
            `;
            
            summary.skipped_invoices.forEach(invoice => {
                html += `<li>${invoice}</li>`;
            });
            
            html += `</ul></div>`;
        }

        // Failed Invoices Section
        if (summary.failed_invoices && summary.failed_invoices.length > 0) {
            html += `
                <div class="summary-section error-section">
                    <div class="section-title">
                        🔴 ${__('Failed Invoices')} (${summary.failed_invoices.length})
                    </div>
                    <ul class="item-list">
            `;
            
            summary.failed_invoices.forEach(invoice => {
                html += `
                    <li>
                        <strong>${invoice.invoice}</strong>: ${invoice.error}
                    </li>
                `;
            });
            
            html += `</ul></div>`;
        }

        // Overall Status
        html += `
            <div class="summary-section" style="background-color: #f8f9fa; border-left-color: #6c757d;">
                <div class="section-title">📊 ${__('Overall Status')}</div>
                <div style="font-size: 13px;">
        `;

        if (summary.successful_count > 0) {
            html += `<p>✅ ${__('Successfully processed {0} invoices', [summary.successful_count])}</p>`;
        }
        if (summary.skipped_count > 0) {
            html += `<p>🟡 ${__('Skipped {0} already paid invoices', [summary.skipped_count])}</p>`;
        }
        if (summary.failed_count > 0) {
            html += `<p>🔴 ${__('Failed to process {0} invoices', [summary.failed_count])}</p>`;
        }

        if (summary.companies_count > 1) {
            html += `<p>🏢 ${__('Processed across {0} companies', [summary.companies_count])}</p>`;
        }

        html += `</div></div>`;
        html += `</div>`; // Close processing-summary div

        return html;
    },

    // Auto-show summary after submit
    after_save: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.status === 'Approved') {
            // Small delay to ensure all processing is complete
            setTimeout(() => {
                frm.trigger('show_processing_summary');
            }, 2000);
        }
    }
});

frappe.ui.form.on('Payment Receipt Details', {
    allocated_amount: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (row.allocated_amount > flt(row.outstanding)) {
            frappe.msgprint(__('Allocated amount cannot be greater than outstanding amount'));
            frappe.model.set_value(cdt, cdn, 'allocated_amount', row.outstanding);
        }
    },

    billing_document: function(frm, cdt, cdn) {
        const row = frappe.get_doc(cdt, cdn);
        if (row.billing_document) {
            // Auto-set allocated amount to outstanding amount if not set
            if (!row.allocated_amount && row.outstanding) {
                frappe.model.set_value(cdt, cdn, 'allocated_amount', row.outstanding);
            }
        }
    }
});

// Add server method to get processing summary
frappe.ui.form.on("Payment Receipt Upload", {
    get_processing_summary: function(frm) {
        return new Promise((resolve) => {
            frappe.call({
                method: 'edubliss.edubliss.doctype.payment_receipt_upload.payment_receipt_upload.get_processing_summary',
                args: {
                    payment_receipt_upload: frm.doc.name
                },
                callback: function(r) {
                    resolve(r.message);
                }
            });
        });
    }
});