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


class dtm_amsj_rotacion_de_productos(models.Model):
    _inherit = 'stock.quant'
    
    @api.depends('in_date')
    @api.multi
    def compute_fecha_indate_texto(self):
        for rec in self:
            if rec.in_date:
                rec.write({'fecha_indate_texto': rec.in_date.strftime('%d/%m/%Y')})

    @api.model
    def create(self, vals):
        ret = super(dtm_amsj_rotacion_de_productos, self).create(vals)
        ret.get_calcular_movs_en_tres_meses()
        return ret

    @api.multi
    def get_calcular_movs_en_tres_meses(self):
        for rec in self:
            hace_tres_meses_time = datetime.now() - timedelta(days=92)  # dos meses de 31 dias y uno de 30
            hace_tres_meses = hace_tres_meses_time.strftime('%Y-%02m-%02d')
            if rec.in_date[:10] > hace_tres_meses:
                rec.write({'movs_en_tres_meses': True})
            else:
                rec.write({'movs_en_tres_meses': False})

    calcular_movs_en_tres_meses = fields.Boolean(string="Solo usado para cargas iniciales",
                                                 compute='get_calcular_movs_en_tres_meses')

    movs_en_tres_meses = fields.Boolean(string=u'Movimientos en los últimos 3 meses')
    fecha_indate_texto = fields.Char(string=u'fecha último movimiento', compute='compute_fecha_indate_texto')


dtm_amsj_rotacion_de_productos()

