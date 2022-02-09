from openerp import models, api,fields

class account_invoice(models.Model):
    _inherit='account.invoice'


    def func_vacia(self):
        return