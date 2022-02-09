openerp.dtm_amsj_seguridad_productos = function(openerp) {
    "use strict";
    //let FormView = require('web.FormView');
    openerp.web.FormView.include({
        load_record: function (record) {
            console.log('test')
            if (record && this.$buttons && this.get('actual_mode') === 'view') {


                if (record.hide_action_buttons) {
                    //this.$buttons.find('.o_form_buttons_view').hide();
                    this.$buttons.find('.oe_form_button_edit').hide();
                    this.$buttons.find('.oe_form_button_edit').prop("disabled", true);
                     this.$buttons.find('.oe_form_button_create').hide();
                    this.$buttons.find('.oe_form_button_create').prop("disabled", true);
                    
                } else {
                    //this.$buttons.find('.o_form_buttons_view').show();
                    this.$buttons.find('.oe_form_button_edit').show();
                    this.$buttons.find('.oe_form_button_edit').prop("disabled", false);
                    this.$buttons.find('.oe_form_button_create').show();
                    this.$buttons.find('.oe_form_button_create').prop("disabled", false);
                }
            }
            return this._super(record);
        }
    });
}

