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
            frappe.web_form.set_value("date_of_birth", data.date_of_birth);
            frappe.web_form.set_value("academic_year", data.academic_year);
            frappe.web_form.set_value("academic_term", data.academic_term);
            
            // DEBUG: Log document data
            console.log("Document data received:", {
                applicants_passport: data.applicants_passport,
                image: data.image,
                immunization_card: data.immunization_card,
                fathers_passport: data.fathers_passport,
                mothers_passport: data.mothers_passport,
                fathers_id_card: data.fathers_id_card,
                mothers_id_card: data.mothers_id_card,
                emergency_contact_passport: data.emergency_contact_passport,
                previous_school_result: data.previous_school_result,
                transfer_certificate: data.transfer_certificate
            });
            
            // CORRECTED: Populate document checklist with proper checks
            populateDocumentChecklist(data);
            
            // Setup parent auto-fill after form is populated
            setupParentAutoFill();
        }
    });

    // FUNCTION TO PROPERLY POPULATE DOCUMENT CHECKLIST
    function populateDocumentChecklist(data) {
        // Birth Certificate - Check if it has a value (not just exists)
        if (data.birth_certificate && data.birth_certificate !== "0" && data.birth_certificate !== 0) {
            frappe.web_form.set_value("birth_certificate", 1);
            console.log("Birth Certificate: CHECKED");
        } else {
            frappe.web_form.set_value("birth_certificate", 0);
            console.log("Birth Certificate: NOT CHECKED");
        }
        
        // Applicants Passport - Check both fields
        if ((data.applicants_passport && data.applicants_passport !== "0" && data.applicants_passport !== 0) || 
            (data.image && data.image !== "")) {
            frappe.web_form.set_value("applicants_passport", 1);
            console.log("Applicants Passport: CHECKED");
        } else {
            frappe.web_form.set_value("applicants_passport", 0);
            console.log("Applicants Passport: NOT CHECKED");
        }
        
        // Immunization Card
        if (data.immunization_card && data.immunization_card !== "0" && data.immunization_card !== 0) {
            frappe.web_form.set_value("immunization_card", 1);
            console.log("Immunization Card: CHECKED");
        } else {
            frappe.web_form.set_value("immunization_passport", 0);
            console.log("Immunization Card: NOT CHECKED");
        }
        
        // Previous School Result
        if (data.previous_school_result && data.previous_school_result !== "0" && data.previous_school_result !== 0) {
            frappe.web_form.set_value("previous_school_result", 1);
            console.log("Previous School Result: CHECKED");
        } else {
            frappe.web_form.set_value("previous_school_result", 0);
            console.log("Previous School Result: NOT CHECKED");
        }
        
        // Transfer Certificate
        if (data.transfer_certificate && data.transfer_certificate !== "0" && data.transfer_certificate !== 0) {
            frappe.web_form.set_value("transfer_certificate", 1);
            console.log("Transfer Certificate: CHECKED");
        } else {
            frappe.web_form.set_value("transfer_certificate", 0);
            console.log("Transfer Certificate: NOT CHECKED");
        }
        
        // Parents Passport - Check both father and mother
        if ((data.fathers_passport && data.fathers_passport !== "0" && data.fathers_passport !== 0) || 
            (data.mothers_passport && data.mothers_passport !== "0" && data.mothers_passport !== 0)) {
            frappe.web_form.set_value("parents_passport", 1);
            console.log("Parents Passport: CHECKED");
        } else {
            frappe.web_form.set_value("parents_passport", 0);
            console.log("Parents Passport: NOT CHECKED");
        }
        
        // Parents ID Card - Check both father and mother
        if ((data.fathers_id_card && data.fathers_id_card !== "0" && data.fathers_id_card !== 0) || 
            (data.mothers_id_card && data.mothers_id_card !== "0" && data.mothers_id_card !== 0)) {
            frappe.web_form.set_value("parents_id_card", 1);
            console.log("Parents ID Card: CHECKED");
        } else {
            frappe.web_form.set_value("parents_id_card", 0);
            console.log("Parents ID Card: NOT CHECKED");
        }
        
        // Emergency Contact Passport
        if (data.emergency_contact_passport && data.emergency_contact_passport !== "0" && data.emergency_contact_passport !== 0) {
            frappe.web_form.set_value("emergency_contact_passport", 1);
            console.log("Emergency Contact Passport: CHECKED");
        } else {
            frappe.web_form.set_value("emergency_contact_passport", 0);
            console.log("Emergency Contact Passport: NOT CHECKED");
        }
    }

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
    
    // Add CSS to make checked items more visible
    const style = document.createElement('style');
    style.textContent = `
        /* Highlight checked documents */
        [data-fieldname^="birth_certificate"] input[type="checkbox"]:checked,
        [data-fieldname^="applicants_passport"] input[type="checkbox"]:checked,
        [data-fieldname^="immunization_card"] input[type="checkbox"]:checked,
        [data-fieldname^="previous_school_result"] input[type="checkbox"]:checked,
        [data-fieldname^="transfer_certificate"] input[type="checkbox"]:checked,
        [data-fieldname^="parents_passport"] input[type="checkbox"]:checked,
        [data-fieldname^="parents_id_card"] input[type="checkbox"]:checked,
        [data-fieldname^="emergency_contact_passport"] input[type="checkbox"]:checked {
            background-color: #10b981 !important;
            border-color: #10b981 !important;
        }
        
        /* Style for checked label */
        .frappe-control input[type="checkbox"]:checked + label {
            color: #10b981;
            font-weight: 600;
        }
        
        /* Document section styling */
        [data-fieldname="section_break_6vq8"] {
            background-color: #f0f9ff !important;
            border-left: 4px solid #0ea5e9 !important;
        }
        
        [data-fieldname="section_break_6vq8"] .section-head {
            color: #0369a1 !important;
        }
        
        /* Make checkboxes larger for better visibility */
        .frappe-control input[type="checkbox"] {
            width: 18px !important;
            height: 18px !important;
            margin-right: 8px !important;
        }
    `;
    document.head.appendChild(style);
});