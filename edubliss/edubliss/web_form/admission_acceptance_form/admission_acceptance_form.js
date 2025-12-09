frappe.ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const admission_enquiry_no = urlParams.get("admission_enquiry_no");
    const program = urlParams.get("program");

    if (!admission_enquiry_no && !program) {
        frappe.show_alert("No Enquiry no and Program found");
        return;
    }

    if (!admission_enquiry_no || !program) {
        frappe.show_alert("No Enquiry no or Program found");
        return;
    }

    let leadData = null;

    // Fetch lead details
    frappe.call({
        method: "edubliss.api.get_lead_details",
        args: { admission_enquiry_no },
        callback: function (r) {
            if (!r.message) return;

            const data = r.message;
            leadData = data;

            // Populate student information
            frappe.web_form.set_value("admission_enquiry_no", data.admission_enquiry_no);
            frappe.web_form.set_value("student_first_name", data.student_first_name);
            frappe.web_form.set_value("student_last_name", data.student_last_name);
            frappe.web_form.set_value("student_full_name", data.student_full_name);
            frappe.web_form.set_value("program", data.program);
            frappe.web_form.set_value("gender", data.gender);
            frappe.web_form.set_value("academic_year", data.academic_year);
            frappe.web_form.set_value("academic_term", data.academic_term);
            
            // Populate document checklist
            if (data.applicants_passport || data.image) frappe.web_form.set_value("applicants_passport", 1);
            if (data.immunization_card) frappe.web_form.set_value("immunization_card", 1);
            if (data.fathers_passport || data.mothers_passport) frappe.web_form.set_value("parents_passport", 1);
            if (data.fathers_id_card || data.mothers_id_card) frappe.web_form.set_value("parents_id_card", 1);
            if (data.emergency_contact_passport) frappe.web_form.set_value("emergency_contact_passport", 1);
            if (data.previous_school_result) frappe.web_form.set_value("previous_school_result", 1);
            if (data.transfer_certificate) frappe.web_form.set_value("transfer_certificate", 1);

            // Setup parent auto-fill after form is populated
            setupParentAutoFill();
        }
    });

    // SIMPLE PARENT AUTO-FILL FUNCTION
    function setupParentAutoFill() {
        // Wait a moment for the form to render
        setTimeout(() => {
            const relationshipField = frappe.web_form.fields_dict.relationship_to_student;
            if (relationshipField && relationshipField.input) {
                relationshipField.input.addEventListener('change', function(e) {
                    handleRelationshipChange(e.target.value);
                });
                
                console.log("Parent auto-fill ready");
            }
        }, 500);
    }
    
    function handleRelationshipChange(value) {
        if (!leadData) {
            console.log("No lead data available");
            return;
        }
        
        if (value === 'Father') {
            if (leadData.fathers_name) frappe.web_form.set_value("full_name", leadData.fathers_name);
            if (leadData.fathers_mobile_no) frappe.web_form.set_value("phone_number", leadData.fathers_mobile_no);
            if (leadData.email_id) frappe.web_form.set_value("email", leadData.email_id);
            frappe.show_alert("Father's information loaded", 3);
        } 
        else if (value === 'Mother') {
            if (leadData.mothers_name) frappe.web_form.set_value("full_name", leadData.mothers_name);
            if (leadData.mothers_mobile_no) frappe.web_form.set_value("phone_number", leadData.mothers_mobile_no);
            if (leadData.mothers_email) frappe.web_form.set_value("email", leadData.mothers_email);
            frappe.show_alert("Mother's information loaded", 3);
        }
    }
});