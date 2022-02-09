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

import logging

from openerp import models, fields, exceptions, api, _

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


class dtm_amsj_dias_repeticion(models.TransientModel):
    _name = "dtm.amsj.dias.repeticion"

    file = fields.Binary('Archivo CSV')

    columna_producto = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                         ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                         ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                         ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                        string="Nro. columna Ref. interna producto", default='0')

    columna_especialidad = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                             ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                             ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                             ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                            string="Nro. columna codigo de Especialidad", default='1')

    columna_dias = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                     ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                     ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                     ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                    string="Nro. columna días", default='2')

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

        indx_pro = int(self.columna_producto)
        indx_especialidad = int(self.columna_especialidad)
        indx_dias = int(self.columna_dias)

        dias_chequeo = None
        for i in lineas:

            i = i.replace('\r', '')
            i = i.replace('\n', '')

            # Separando los datos del movimiento
            mov = i.split(';')

            if len(mov) == 3:
                dias_chequeo = mov[indx_dias].isdigit()

            if len(mov) == 3 and dias_chequeo:

                cod_prod = mov[indx_pro]
                dias = int(mov[indx_dias])
                especialidad = mov[indx_especialidad]

                tipo_de_empaque = self.env['tipo.empaque'].search([('name', '=', 'Caja')],limit=1)

                categoria_id = self.env['categoria'].search([('CodigoAMSJ', '=', '0')],limit=1)

                prod = self.env['product.product'].search([('default_code', '=', cod_prod)])

                prod = [x.product_tmpl_id.id for x in prod]

                p_tempalte = self.env['product.template'].search(
                    [('id', 'in', prod),
                     ('tipo_de_empaque', '=', tipo_de_empaque.id)])

                ids_templates = [r.id for r in p_tempalte]

                especial = self.env['especialidad'].search([('CodigoAMSJ', '=', especialidad)],limit=1)

                existe = self.env['dias_de_repeticion'].search(
                    [('producto_id', 'in', ids_templates), ('name', '=', especial.id)])
                existe_ids = [n.id for n in existe]

                if len(existe) > 0:

                    for ids in existe_ids:
                        sql = '''UPDATE dias_de_repeticion 
                            set dias=%(dias)s
                            where id = %(existe)s; '''
                        self.env.cr.execute(sql, {'dias': dias, 'existe': ids})

                if len(ids_templates) > 0 and len(existe_ids) == 0:
                    carga = {
                        'name': especial.id,
                        'producto_id': p_tempalte.id,
                        'dias': dias
                    }

                    self.env['dias_de_repeticion'].create(carga)

            if len(mov) <= 1:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Notificación',
                    'params': {
                        'title': 'Día de repeticion',
                        'text': 'Se cargaron los días correctamente',
                        'sticky': False
                    }
                }
