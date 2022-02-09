#  -*- coding: utf-8 -*-
from openerp import models,fields,api
import openerp.tools as tools




class dtm_amsj_informe_consumos_dinamico(models.Model):
    _name = "dtm.amsj.informe.consumos.dinamico"


    codigo = fields.Char(string='Codigo')
    producto = fields.Char(string='Producto')
    cantidad = fields.Integer(string="Cantidad")
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    fecha = fields.Date(string='Fecha')


