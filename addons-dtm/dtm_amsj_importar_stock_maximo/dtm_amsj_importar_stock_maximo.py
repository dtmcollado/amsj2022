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
import logging
import codecs
import base64
from datetime import datetime, timedelta
import time
from openerp.exceptions import ValidationError

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


class dtm_amsj_importar_stock_maximo(models.Model):
    _name = "dtm.amsj.importar.stock.maximo"

    file = fields.Binary('Archivo CSV')
    ubicacion = fields.Many2one('stock.location', string='Ubicación')
    bandera = fields.Boolean(string='activador', default=True)
    archivo_nombre = fields.Char('')
    archivo_contenido = fields.Binary(string="Archivo de Ejemplo")

    archivo_para_errores = fields.Char('')
    archivo_errores_contenidos = fields.Binary(string="Error?")
    mostrar = fields.Char('')
    sector_id = fields.Many2one('categoria', string="Sector", requiered=True)

    # creacion de archivo de ejemplo
    @api.onchange('bandera')
    def _onchange_bandera(self):
        self.archivo_nombre = u'Archivo de ejemplo IMPORTAR STOCK MÁXIMO.CSV'
        dato = 'Referencia_interna;Codigo_AMSJ_Ubicacion;Cantidad' + '\n'
        dato += '36704;SJMFAR;20' + '\n'
        dato += '18200;LIBFAR;15'
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
            raise exceptions.Warning(_(u"Archivo con formato inválido"))

        # Decodificación y separación en líneas
        lineas = base64.b64decode(self.file)
        lineas = lineas.split('\n')

        # Recibo desde el archivo las siguientes variables
        ref_interna = None
        codigo_amsj = None
        cantidad = 1

        no_titulo = None
        lista_errores = []

        # Variables para cargar a la base
        ubicacion_stockcritico = {'ajuste_manual': None,
                                  'stock_critico': None,
                                  'product_tmpl_id': None,
                                  'ubicacion_id': None, }

        cantidad_registros = 0
        linea = 0
        # ejemplo:[ajuste_manual,product_tmpl_id,stock_critico(cantidad), ubicacion_id]

        for i in lineas:

            i = i.replace('\r', '')
            i = i.replace('\n', '')

            if linea >= 1:
                ref_interna = None
                codigo_amsj = None

                # Separando los datos del movimiento
                mov = i.split(';')

                # chequeo que no haya titulos

                if len(mov) >= 2:

                    if mov[0]:
                        ref_interna = mov[0]
                    if mov[1]:
                        codigo_amsj = mov[1]
                    if mov[2]:
                        cantidad = float(mov[2])

                    ubic = self.env['stock.location'].search([('codigo_amsj', '=', codigo_amsj)])

                    # producto=self.env['product.product'].search([('default_code','=',ref_interna)])
                    p_id = None
                    producto = None
                    sql_prod = '''select p.id from product_product p
                     inner join product_template pt on pt.id = p.product_tmpl_id
                      where default_code =  %(default_code)s and pt.categoria_id = %(categoria)s  and
                       pt.tipo_de_empaque <> 2'''

                    self.env.cr.execute(sql_prod, {'default_code': ref_interna, 'categoria': self.sector_id.id})
                    sql_resultado = self.env.cr.fetchall()

                    if sql_resultado:
                        p_id = sql_resultado[0][0]
                        producto = sql_resultado[0][0]

                    if not ubic and not self.ubicacion:
                        aux = (u'No se encontró la ubicación ', codigo_amsj, u' - línea Nro' + str(linea), i)
                        lista_errores.append(aux)
                    if not producto:
                        aux = (u'No se encontró el producto ', ref_interna, u' - línea Nro' + str(linea), i)
                        lista_errores.append(aux)

                    if producto and (ubic or self.ubicacion):

                        prod_tmpl = self.env['product.product'].search([('id', '=', p_id)])

                        ubicacion_final = None

                        if not self.ubicacion:
                            # ubic = self.env['stock.location'].search([('codigo_amsj', '=', codigo_amsj)])
                            sql_ubicacion = '''select id from stock_location where codigo_amsj = %(codigo_amsj)s '''
                            self.env.cr.execute(sql_ubicacion, {'codigo_amsj': codigo_amsj})
                            ubic = self.env.cr.fetchall()

                            if ubic:
                                ubicacion_final = ubic[0][0]

                            else:
                                aux = (u'No se encontró la ubicación ', codigo_amsj, u' - línea ' + str(linea), i)
                                lista_errores.append(aux)

                        if self.ubicacion:
                            ubicacion_final = self.ubicacion.id

                        # existe=self.env['ubicacion.stockcritico'].search([('product_tmpl_id','=',prod_tmpl.product_tmpl_id.id),('ubicacion_id','=',ubicacion_final)])
                        sql_existe_critico = ''' select id from ubicacion_stockcritico where product_tmpl_id = %(tmpl_id)s and ubicacion_id = %(ubi)s '''
                        # print producto, prod_tmpl.product_tmpl_id.id if  prod_tmpl.product_tmpl_id.id else 0

                        existe = None

                        if prod_tmpl:
                            self.env.cr.execute(sql_existe_critico,
                                                {'tmpl_id': prod_tmpl.product_tmpl_id.id, 'ubi': ubicacion_final})
                            existe = self.env.cr.fetchall()

                        if existe:
                            # existe.write({'stock_critico':cantidad})
                            existe = existe[0][0]
                            # sql_existe_update = '''UPDATE ubicacion_stockcritico
                            #                             set stock_critico=%(cantidad)s
                            #                             where id = %(existe)s '''
                            # self.env.cr.execute(sql_existe_update, {'existe': existe, 'cantidad': cantidad})
                            stock_maximo_id = self.env['ubicacion.stockcritico'].search([('id', '=', existe)])
                            stock_maximo_id.write({'ajuste_manual': False,
                                                   'stock_critico': cantidad,
                                                   'product_tmpl_id': prod_tmpl.product_tmpl_id.id,
                                                   'ubicacion_id': ubicacion_final, })

                        if not existe and ubicacion_final and prod_tmpl:
                            #          sql_stock_cri = '''INSERT INTO ubicacion_stockcritico(
                            #          ajuste_manual, stock_critico, product_tmpl_id, ubicacion_id)
                            # VALUES(%(ajuste_manual)s, %(stock_critico)s, %(product_tmpl_id)s, %(ubicacion_id)s)'''

                            ubicacion_stockcritico = {'ajuste_manual': False,
                                                      'stock_critico': cantidad,
                                                      'product_tmpl_id': prod_tmpl.product_tmpl_id.id,
                                                      'ubicacion_id': ubicacion_final, }

                            # self.env.cr.execute(sql_stock_cri, ubicacion_stockcritico)
                            self.env['ubicacion.stockcritico'].create(ubicacion_stockcritico)
                        cantidad_registros += 1

                if len(mov) <= 1:
                    registros = str(cantidad_registros)
                    aux = "Se importaron exitosamente %s registros" % (registros)

                    if len(lista_errores) > 0:
                        mensaje = u'No se importaron las siguientes líneas:\n'
                        for i in lista_errores:
                            mensaje += ("%s, %s, %s,--> %s \n") % (i[0], i[1], i[2], i[3])

                        self.archivo_para_errores = u'- Error en la importación de Stock máximo'
                        dato_error = aux + '\n'
                        dato_error += mensaje

                        data_to_save_error = codecs.encode(dato_error, 'utf-8')
                        # data_to_save_error = codecs.decode(dato_error, 'cp1252')
                        data_to_save_error = base64.encodestring(data_to_save_error)

                        self.archivo_errores_contenidos = data_to_save_error


                    else:
                        # raise Warning ('Importación de lotes:',aux)

                        self.mostrar = 'Se importaron %s registros correctamente' % registros
            linea += 1
