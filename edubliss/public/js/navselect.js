function submitForm() {
    // Get selected values
    var company = document.getElementById('company').value;
    var academic_year = document.getElementById('academic_year').value;
    var academic_term = document.getElementById('academic_term').value;

    // Call Frappe API to submit the selected values
    frappe.call({
        method: 'your_custom_app.api.process_selected_values',
        args: {
            company: company,
            academic_year: academic_year,
            academic_term: academic_term
        },
        callback: function(response) {
            if (response.message) {
                alert('Selected Data: ' + JSON.stringify(response.message));
                // You can also handle the response data and use it in your webpage as needed
                // For example, updating a part of the page with the response data
            } else {
                alert('Failed to retrieve data.');
            }
        }
    });

    // Prevent form submission
    return false;
}