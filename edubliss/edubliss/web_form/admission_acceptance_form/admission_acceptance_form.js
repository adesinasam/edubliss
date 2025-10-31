// frappe.ready(function() {
// 	// bind events here
// })

frappe.ready(function() {
    // Get admission_enquiry_no from URL parameters using URLSearchParams
    const urlParams = new URLSearchParams(window.location.search);
    const admission_enquiry_no = urlParams.get('admission_enquiry_no');
    
    console.log('URL Parameter:', admission_enquiry_no);
    
    if (admission_enquiry_no) {
        // Set the admission_enquiry_no field value
        frappe.web_form.set_value('admission_enquiry_no', admission_enquiry_no);
        
        // Fetch and populate related data from Lead
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Lead',
                name: admission_enquiry_no
            },
            callback: function(response) {
                if (response.message) {
                    const lead = response.message;
                    console.log('Lead data loaded:', lead);
                    
                    // Set the field values
                    frappe.web_form.set_value('student_first_name', lead.first_name || '');
                    frappe.web_form.set_value('student_last_name', lead.last_name || '');
                    
                    // Set full name - use lead_name if available, otherwise combine first + last
                    const full_name = lead.lead_name || 
                                    ((lead.first_name || '') + ' ' + (lead.last_name || '')).trim();
                    frappe.web_form.set_value('student_full_name', full_name);
                    
                    frappe.web_form.set_value('program', lead.program );
                    frappe.web_form.set_value('gender', lead.gender);
                    frappe.web_form.set_value('academic_year', lead.custom_desired_academic_year );
                    frappe.web_form.set_value('academic_term', lead.custom_desired_academic_term );
                    
                } else {
                    frappe.show_alert({
                        message: __('Admission Enquiry not found: ' + admission_enquiry_no),
                        indicator: 'red'
                    });
                }
            },
            error: function(err) {
                console.error('Error loading lead:', err);
                frappe.show_alert({
                    message: __('Error loading student information'),
                    indicator: 'red'
                });
            }
        });
    } else {
        console.log('No admission_enquiry_no parameter found in URL');
        frappe.show_alert({
            message: __('No Admission Enquiry number provided in URL'),
            indicator: 'yellow'
        });
    }
});