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

from openerp import api, models
from ..library import formatters
from datetime import datetime


class ParticularReport(models.AbstractModel):
    _inherit = 'report.abstract_report'
    _name = 'report.dtm_amsj_conusmo_de_productos.invoices_conformar'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']

        report = report_obj._get_report_from_name('dtm_amsj_conusmo_de_productos.invoices_conformar')

        wizard = self.env['wizard.pdf'].browse(self._context.get('active_ids', []))

        finicio = formatters.date_fmt(wizard.fecha_inicial)
        ffinal = formatters.date_fmt(wizard.fecha_final)

        rango_fechas = 'Fecha desde ' + finicio + ' a ' + ffinal

        sectores = ''
        for sector in wizard.sector_ids:
            sectores += sector.name + '/'

        if wizard.sector_todos or not wizard.sector_ids:
            filtro_1 = 'Productos de todos los sectores'
        else:
            filtro_1 = 'Productos del sector: (' + sectores + ')'

        categorias = ''
        for categoria in wizard.categoria_ids:
            categorias += categoria.name + '/'
        if wizard.categoria_ids:
            filtro_2 = 'Productos de la categoria: (' + categorias + ')'
        else:
            filtro_2 = 'Productos de todas las categorias'

        if not wizard.origen_ids:
            filtro_3 = 'Todos los Origenes'
        else:
            origenes = ""
            for origen in wizard.origen_ids:
                origenes += origen.display_name + '/'
            if wizard.origen_ids:
                filtro_3 = 'Origenes: (' + origenes + ')'
            else:
                filtro_3 = 'Todos los Origenes'

        # wizard.obra.id

        now = datetime.now()
        # print()
        salida = formatters.current_date_format(now)

        fecha = 'San José de Mayo, ' + salida + '.'

        meses = {'01': 'Enero',
                 '02': 'Febrero',
                 '03': 'Marzo',
                 '04': 'Abril',
                 '05': 'Mayo',
                 '06': 'Junio',
                 '07': 'Julio',
                 '08': 'Agosto',
                 '09': 'Setiembre',
                 '10': 'Octubre',
                 '11': 'Noviembre',
                 '12': 'Diciembre',
                 }
        anio = datetime.strptime(wizard.fecha_inicial, '%Y-%m-%d').strftime('%Y')
        mes = meses.get(datetime.strptime(wizard.fecha_inicial, '%Y-%m-%d').strftime('%m'))

        mensaje = """
        Por la presente se informa los montos de los bienes de tipo almacenable 
        enviados a consumo correspondientes a """ + mes + """ de """ + anio + """, de los siguientes rubros del sector """ + sector.display_name + """ :"""

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': wizard,
            'report_title': fecha,
            'report_mensaje': mensaje,
            'rango_fechas': rango_fechas,
            'filtro_1': filtro_1,
            'filtro_2': filtro_2,
            'filtro_3': filtro_3,
            'wizard': wizard,
            'currency_fmt': formatters.currency_fmt,
            'date_fmt': formatters.date_fmt,
            'lineas': data['lineas']
        }
        return report_obj.render('dtm_amsj_conusmo_de_productos.invoices_conformar', docargs)


ParticularReport()
