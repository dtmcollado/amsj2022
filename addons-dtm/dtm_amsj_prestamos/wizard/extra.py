from openerp import models, fields, api

class confirm_wizard(models.TransientModel):
    _name = 'tjara.confirm_wizard'

    yes_no = fields.Char(default='Do you want to proceed?')

    @api.multi
    def yes(self):
        return True

    @api.multi
    def no(self):
        return False

