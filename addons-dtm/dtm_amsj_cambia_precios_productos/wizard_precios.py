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

from datetime import date
from datetime import date
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
import logging


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

class scheduler_amsj(models.Model):
    _name = 'scheduler.amsj'

    name = fields.Char(string='Nombre', readonly=True)
    ejecuto_bien = fields.Boolean(string='Se actualizo', readonly=True)
    fecha = fields.Date(string='Fecha', readonly=True)

    def process_amsj_scheduler_queue(self, cr, uid, context=None):
        scheduler_line_obj = self.pool.get('scheduler.amsj')

        scheduler_line_ids = self.pool.get('scheduler.amsj').search(cr, uid, [])

        for scheduler_line_id in scheduler_line_ids:
            scheduler_line = scheduler_line_obj.browse(cr, uid, scheduler_line_id, context=context)
            # numberOfUpdates = scheduler_line.numberOfUpdates
            _logger.info('line: ' + scheduler_line.name)
            # scheduler_line_obj.write(cr, uid, scheduler_line_id, {'numberOfUpdates': (numberOfUpdates + 1),
            #                                                       'lastModified': datetime.date.today()},
            #                          context=context)

    @api.multi
    def process_amsj_scheduler_precios(self):
        pendientes = self.env['dtm.precios.costo.importados'].search(
            [('state', '!=', 'done')])
        encontre = False
        for pendiente in pendientes:
            encontre = True
            if pendiente.precio_costo != pendiente.product_id.standard_price:
                pendiente.product_id.write({'standard_price': pendiente.precio_costo})

            pendiente.write({'state': 'done'})

        if encontre:
            vals = {}
            vals['fecha'] = date.today()
            vals['name'] = "Ejecuto scheduler Precios"
            vals['ejecuto_bien'] = True
            self.create(vals)
        else:
            vals = {}
            vals['fecha'] = date.today()
            vals['name'] = "Ejecuto precios SIN DATOS"
            vals['ejecuto_bien'] = False
            self.create(vals)
        return



class dtm_precios_importados(models.Model):
    _name = "dtm.precios.costo.importados"

    product_id = fields.Many2one('product.template', string='Producto',
                                 ondelete='restrict', index=True, readonly=True
                                 )
    fecha = fields.Date('Begin date', default=date.today())
    precio_costo = fields.Float(string='Precio de Costo', readonly=True)

    state = fields.Selection([
        ('draft', 'Pendiente'),
        ('done', u'Actualizado')
    ],
        string='Estado', index=True, readonly=True,
        default='draft', copy=False)

    # @api.multi
    # def actualiza_precios(self):
    #     pendientes = self.env['dtm.precios.costo.importados'].search(
    #         [('state', '=', 'draft')])
    #
    #     for pendiente in pendientes:
    #         pendiente.write({'state': 'done'})


class amsj_precios(models.TransientModel):
    _name = "amsj.precios"

    file = fields.Binary('Archivo CSV')
    
    columna_producto = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                         ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                         ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                         ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                        string="Nro. columna Ref. interna producto", default='0')

   

    columna_importe = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                        ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                        ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                        ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                       string="Nro. columna Importe Unitario", default='1')


    @api.multi
    def import_csv(self):
        data = base64.b64decode(self.file)
        #verifico el archivo
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.reader(file_input, delimiter=';')

        try:
            reader_info.extend(reader)

        except Exception:
            raise exceptions.Warning(_("Archivo con formato invalido"))

        #obtengo el archivo 
        #Decodificación y separación en líneas
        lineas = base64.b64decode(self.file)
        lineas = lineas.split('\n')
        
        indx_pro = int(self.columna_producto)
        
        indx_importe = int(self.columna_importe)

        # linea_posibe_vacia=False
        
        for i in lineas:
           
            # Separando los datos del movimiento
            mov = i.split(';')

            if len(mov) > 1:
            
                cod_interno = mov[indx_pro]
                importe = float(mov[indx_importe].replace(',', '.'))


                # product.template
                # standard_price

                # Buscar producto

                if importe > 0:
                    products = self.env['product.template'].search([
                        ('default_code', '=', cod_interno),
                        ('purchase_ok', '=', 'True'),
                        ('categoria_id', '=', 17),  # Farmacia 17
                    ])

                    if products:
                        #product_ids.write({'standard_price': importe})

                        # self.env['dtm.precios.costo.importados'].create({
                        #     'product_id': product_ids .id,
                        #     'precio_costo': importe
                        # })

                        for product in products:
                            self.env.cr.execute(
                                'UPDATE IR_PROPERTY SET value_float = %s WHERE res_id = %s AND name = %s',
                                (importe, 'product.template,'+str(product.id), 'standard_price'))

                            sql_stock = '''INSERT INTO  dtm_precios_costo_importados(
                                                    create_uid, 
                                                    create_date,
                                                     product_id,
                                                    precio_costo,
                                                     fecha,
                                                      state)
                                                                              VALUES(%(x_1)s,
                                                                                     %(x_2)s,
                                                                                      %(x_3)s,
                                                                                      %(x_4)s,
                                                                                      %(x_5)s,
                                                                                      %(x_6)s
                                                                                      );'''

                            parametros = {
                                'x_1': 1,
                                'x_2': date.today(),
                                'x_3': product.id,
                                'x_4': importe,
                                'x_5': date.today(),
                                'x_6': 'draft',
                            }

                            # create_date
                            # product_qty

                            self.env.cr.execute(sql_stock, parametros)

        # if len(mov) <= 1:
        return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Notificación',
                    'params': {
                        'title': 'Precios',
                        'text': 'Los precios se actualizaran en la proximos minutos.',
                        'sticky': False
                    }
                }

        



       




            






        
