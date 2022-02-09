# -*- coding: utf-8 -*-

from openerp import models, api, fields

import logging
import codecs

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


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    csv_archivo_nombre = fields.Char('')
    csv_archivo_contenido = fields.Binary(string="Archivo de Ejemplo")

    @api.multi
    def do_csv(self):

        # aux.filiales

        ubicacion = self.env['aux.filiales'].search(
            [
                ('almacen_id', '=', self.location_dest_id.almacen_id.id)
            ], limit=1)
        ubi_cobol = ubicacion.codigo_cobol

        self.csv_archivo_nombre = u'cobols.CSV'
        dato = 'CodigoMSP;Cantidad;Filial;IdOdoo' + '\n'
        for xmove in self.move_lines:
            if xmove.state == 'done':
                codigo = xmove.product_id.default_code
                cantidad = int(xmove.product_qty)
                dato += str(codigo) + ';' + str(cantidad) + ';' + str(ubi_cobol) + ';' + str(xmove.id) + '\n'

        data_to_save = codecs.encode(dato, 'cp1252')
        data_to_save = base64.encodestring(data_to_save)
        self.csv_archivo_contenido = data_to_save

        self.write({'csv_archivo_contenido': data_to_save})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=stock.picking&field=csv_archivo_contenido&id=%s&filename=cobol.csv' % (
            self.id,),
            'target': 'self',
        }
