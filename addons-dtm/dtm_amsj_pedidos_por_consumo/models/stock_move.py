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

import os
import base64

import xlwt
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO
from openerp import tools


class dtm_amsj_move(models.Model):
    _inherit = 'stock.move'

    # lot_id = fields.Many2one('stock.production.lot', 'Lot')
    # life_date = fields.Datetime(string='Life Date', related='lot_id.life_date')
    lote = fields.Char('Lote')


dtm_amsj_move()


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc"

    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")


    @api.multi
    def action_planilla(self):
        # Creo el libro Excel
        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)

        # Estilos
        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        header = easyxf('font: name Calibri, bold True; alignment: horizontal center;')
        """
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')
        """

        fila = 0

        # Datos de la empresa y fecha de emision
        # ws.row(fila).height = 2 * 200
        # ws.write_merge(fila, fila, 3, 7, self.descripcion, title_big)

        fila += 1

        fuente = Font()
        fuente.name = "Calibri"
        estilo = XFStyle()
        estilo.font = fuente

        # Escribo el titulo de cada columna
        # La última columna es para el color
        # titulos = [descrip[0] for descrip in self.env.cr.description][:-1]
        #
        # for i, titulo in enumerate(titulos):
        #     ws.write(fila, i, titulo, header)


        for linea in self.move_lines:
            #
            #
            #
            ws.write(fila, 0, linea.product_id.display_name, estilo)
            ws.write(fila, 1, linea.product_qty, estilo)
            ws.write(fila, 2, linea.lote, estilo)
            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 34,
            1: 10,
            2: 20,

        }

        for col in range(0, 3):
            ws.col(col).width = anchos.get(col, 7) * 367

        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Compras.xlsx",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=stock.picking&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }


StockPicking()
