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

from datetime import date, timedelta, datetime
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
from datetime import datetime

import logging
import os, sys
import zlib

_logger = logging.getLogger(__name__)

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

CODIGO_FARMACIA = 17


class gen_cobol(models.TransientModel):
    _name = "gen.cobol"

    file = fields.Binary('Archivo CSV')
    file_name = fields.Char("File Name")
    name = fields.Char(string='Referencia', index=True)
    almacen = fields.Many2one('aux.filiales', string='Filial' , required=True)

    @api.multi
    def import_csv_cobol(self):
        archivo = self.file
        data = base64.b64decode(self.file)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.reader(file_input, delimiter=';')

        try:
            reader_info.extend(reader)

        except Exception:
            raise Warning(u'Archivo con formato invalido')

        fecha = datetime.now()


        cab = self.env['dtm.amsj.consumos.cobol'].search(
            [
                    ('name', '=', self.file_name),
                    ('state', '=', 'done')
            ], limit=1)

        if cab:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    'title': 'Error',
                    'text': u'Archivo ya fue procesado en la fecha : ' + cab.date ,
                    'sticky': True
                }
            }

        cabezal = self.env['dtm.amsj.consumos.cobol'].create({
            'name': self.file_name,
            'almacen': self.almacen.id
        })

        total_registros = range(len(reader_info))
        error1 = False
        error2 = False

        t = 0
        for i in range(len(reader_info)):
            field = map(str, reader_info[i])
            # values = dict(zip(keys, field))

            if field and i > 0:
                if i == 1:
                    if not field[2] == str(self.almacen.codigo_cobol):
                        cabezal.write({'state': 'error'})
                        return {
                                             'type': 'ir.actions.client',
                                             'tag': 'action_warn',
                                             'name': 'Notificación',
                                             'params': {
                                                 'title': 'Error',
                                                 'text': u'Código de Filial no es correcto',
                                                 'sticky': True
                                             }
                                         }

                try:
                    cod_interno = field[0]
                    cantidad = field[1]
                    cantidad = cantidad.replace('.', '')
                    cantidad = cantidad.replace(',', '')
                    ubicacion = field[2]

                except IndexError:
                    raise Warning(u'Error en valores de las columnas')

                # Buscar producto
                product_id = self.env['product.template'].search([
                    ('default_code', '=', cod_interno),
                    ('purchase_ok', '=', True),
                    ('tipo_de_empaque', '=', 1),
                    ('categoria_id', '=', CODIGO_FARMACIA),  # Farmacia
                ], limit=1)

                if not product_id:
                    product_id_2 = self.env['product.template'].search([
                        ('default_code', '=', cod_interno),
                        ('purchase_ok', '=', True),
                        ('tipo_de_empaque', '=', 2),
                        ('categoria_id', '=', CODIGO_FARMACIA),  # Farmacia
                    ], limit=1)

                    if product_id_2:
                        error1 = True
                    else:
                        error2 = True

                producto_producto = self.env['product.product'].search([('product_tmpl_id', '=', product_id.id)], limit=1)

                try:
                    cant = int(cantidad)

                except ValueError:
                    raise Warning(u'Error en valor de Cantidad de las columna')

                if cabezal and product_id:

                    self.env['dtm.amsj.consumos.cobol.lineas'].create({
                        'name': cod_interno,
                        'quantity': cant,
                        'product_id': producto_producto.id,
                        'importado_id': cabezal.id
                    })

                else:
                    if error1:
                        self.env['dtm.amsj.consumos.cobol.lineas'].create({
                            'name': cod_interno,
                            'quantity': cant,
                            'importado_id': cabezal.id,
                            'state': 'error1',
                        })
                    else:
                        if error2:
                            self.env['dtm.amsj.consumos.cobol.lineas'].create({
                                'name': cod_interno,
                                'quantity': cant,
                                'importado_id': cabezal.id,
                                'state': 'error2',
                            })
                        else:
                            self.env['dtm.amsj.consumos.cobol.lineas'].create({
                                'name': cod_interno,
                                'quantity': cant,
                                'importado_id': cabezal.id,
                            })

        return {
            'target': cabezal.id,
            'name': _('Cobol'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'dtm.amsj.consumos.cobol',
            'view_id': False,
            'type': 'ir.actions.act_window',
        }