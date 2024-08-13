frappe.ui.form.on("Fee Component", {
  item: function(frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    frappe.db.get_value("Item Price", {"item_code": d.item, "price_list": "Standard Selling"}, "price_list_rate", function(value) {
      d.amount = value.price_list_rate;
      d.total = value.price_list_rate;
      frappe.model.set_value(cdt, cdn, 'amount', value.price_list_rate);
      refresh_field("components");
    });
  },
});
