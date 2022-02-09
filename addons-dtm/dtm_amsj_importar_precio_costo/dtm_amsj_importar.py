# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

# from datetime import date, timedelta, time, datetime


from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
import logging
import codecs
import base64
from datetime import datetime, timedelta
import time

_logger = logging.getLogger(__name__)
# import datetime

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')

try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class dtm_amsj_importar_lotes(models.TransientModel):
    _name = "dtm.amsj.importar"

    file = fields.Binary('Archivo CSV')
    ubicacion = fields.Many2one('stock.location', string='Ubicación')
    bandera = fields.Boolean(string='activador', default=True)
    archivo_nombre = fields.Char('')
    archivo_contenido = fields.Binary(string="Archivo de Ejemplo")
    archivo_para_errores = fields.Char('')
    archivo_errores_contenidos = fields.Binary(string="Error?")
    mostrar = fields.Char('')

    # creacion de archivo de ejemplo
    @api.onchange('bandera')
    def _onchange_bandera(self):
        self.archivo_nombre = 'Archivo de ejemplo de importación de Lotes.CSV'
        dato = 'Ref_Interna;Nro_Lote;Vencimiento;Codigo_AMSJ_Ubicacion;Cantidad' + '\n'
        dato += '36704;0000023;2019-12-31;SJMFAR;1' + '\n'
        dato += '36704;0000023;2019-12-31;LIBFAR;5'
        data_to_save = codecs.encode(dato, 'cp1252')
        data_to_save = base64.encodestring(data_to_save)
        self.archivo_contenido = data_to_save

    @api.multi
    def import_csv(self):
        data = base64.b64decode(self.file)
        # verifico el archivo
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.reader(file_input, delimiter=';')

        try:
            reader_info.extend(reader)

        except Exception:
            raise exceptions.Warning(_("Archivo con formato invalido"))

        # Decodificación y separación en líneas
        lineas = base64.b64decode(self.file)
        lineas = lineas.split('\n')
        contador = 0

        for i in lineas:

            puc = 0
            # Separando los datos del movimiento
            mov = i.split(';')
            if len(mov) == 2:

                # chequeo que no haya titulos

                if mov[1]:
                    puc = mov[1]

                if mov[0]:
                    cod_prod = mov[0]

                prod = self.env['product.product'].search([('default_code', '=', cod_prod)])

                prod = [x.product_tmpl_id.id for x in prod]

                p_tempalte = self.env['product.template'].search(
                    [('id', 'in', prod),('tipo_de_empaque', '=', 2),('categoria_id','=',17)], limit=1)


                if p_tempalte:
                    puc = puc.replace(',', '.')
                    if p_tempalte.standard_price != float(puc):
                        # p_tempalte.standard_price = float(puc)
                        vals = {'standard_price': float(puc)}
                        p_tempalte.write(vals)
                        contador = contador + 1
                        print contador