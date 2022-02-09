# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Datamatic All Rights Reserved.
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

import math
import datetime
from openerp import models, api


class CustomReport(models.AbstractModel):
    _name = 'report.dtm_amsj_reporte_movimientos.reporte_movimientos'

    def obtener_data(self, picking_id):
        sql = """
        SELECT sp.id, sq.qty, p.name_template, l.name, COALESCE(l.life_date,now() at time zone 'UYT')::date as life_date
        FROM stock_picking sp
        INNER JOIN stock_move sm on sm.picking_id = sp.id
        INNER JOIN stock_quant_move_rel smr on smr.move_id = sm.id
        INNER JOIN stock_quant sq on sq.id = smr.quant_id
        INNER JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
        INNER JOIN product_product p on p.id = sq.product_id
        INNER JOIN product_template pt on pt.id = p.product_tmpl_id
        WHERE sp.id = %(stock_picking_id)s
        """

        self.env.cr.execute(sql, { 'stock_picking_id': picking_id })
        resultados = self.env.cr.fetchall()

        separado = []
        # id, cantidad, nombre, nombre_lote, fecha_vencimiento
        for index, resultado in enumerate(resultados):
            fecha = resultado[4]
            fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')

            for x in range(0, int(math.ceil(resultado[1] / 30))):
                separado.append({
                    "nombre": resultado[2][0:40],
                    "lote": resultado[3],
                    "fecha": fecha,
                })

        return separado

    @api.model
    def render_html(self, entradas, data=None):
        data = self.obtener_data(entradas[0])
        

        report_obj = self.env['report']
        

        report = report_obj._get_report_from_name('dtm_amsj_reporte_movimientos.reporte_movimientos')
        

        fleet_args = {
            'entradas': data,
            'doc_model': report.model,
            'docs': self,
        }

        
        return report_obj.render('dtm_amsj_reporte_movimientos.reporte_stock_movimientos', fleet_args)
