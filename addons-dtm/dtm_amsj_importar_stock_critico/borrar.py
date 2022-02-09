# -*- coding: utf_8 -*-

from openerp import models, fields

class campo_precio_cocemi(models.Model):
    _inherit = 'product.template'

    precio_cocemi = fields.Float(string='Precios de COCEMI')
    
