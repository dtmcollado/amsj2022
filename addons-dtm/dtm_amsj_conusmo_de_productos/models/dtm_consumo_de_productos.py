# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Datamatic All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from datetime import datetime, date, timedelta
from openerp import tools

class dtm_amsj_consumo_de_productos(models.Model):
    _inherit = 'stock.move'

    @api.model
    def create(self, vals):
        destino = self.env['stock.location'].browse(vals.get('location_dest_id'))
        vals['destino_de_consumo'] = destino.scrap_location
        vals['valor_total'] = float(vals.get('product_qty', 0)) * float(vals.get('price_unit', 0))
        return super(dtm_amsj_consumo_de_productos, self).create(vals)

    @api.multi
    def compute_valor_total(self):
        for rec in self:
            if not rec.valor_total:
                rec.write({'valor_total': rec.product_qty * rec.price_unit})
            if not rec.almacen_origen:
                rec.write({'almacen_origen': rec.location_id.location_id.id})



    @api.one
    @api.depends('date')
    def get_mes(self):
        if self.date:
            meses = {'01': 'enero',
                     '02': 'febrero',
                     '03': 'marzo',
                     '04': 'abril',
                     '05': 'mayo',
                     '06': 'junio',
                     '07': 'julio',
                     '08': 'agosto',
                     '09': 'setiembre',
                     '10': 'octubre',
                     '11': 'noviembre',
                     '12': 'diciembre',
                     }
            try:
                mes = meses.get(datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').strftime('%m'))
            except:
                mes = meses.get(datetime.strptime(self.date, '%Y-%m-%d').strftime('%m'))
            self.mes_calculado = mes
            self.write({'mes': mes})

    @api.one
    @api.depends('date')
    def get_anio(self):
        if self.date:
            try:
                self.anio_calculado = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').strftime('%Y')
            except:
                self.anio_calculado = datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y')
            self.anio = self.anio_calculado
            self.write({'anio': self.anio_calculado})

    centro_costos = fields.Char(string=u"Centro de costos", store=True)
    almacen_origen = fields.Many2one(comodel_name='stock.location', string=u"Almacén", store=True)
    valor_total = fields.Float(string="Precio por Cantidad", store=True)
    
    destino_de_consumo = fields.Boolean(string="La ubicación Destino es de consumo",
                                        related='location_dest_id.scrap_location')

    compute = fields.Boolean(string="solo para cargas", compute='compute_valor_total')

    mes_calculado = fields.Char(string='mes', compute='get_mes')
    mes = fields.Char(string='mes', store=True)
    anio_calculado = fields.Integer(string='mes', compute='get_anio')
    anio = fields.Integer(string=u'año', store=True)


dtm_amsj_consumo_de_productos()
