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
    _name = "dtm.amsj.importar.lotes"

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
        # Recibo desde el archivo las siguientes variables
        ref_interna = None
        nro_lote = None
        vencimiento = None
        codigo_amsj = None
        cantidad = 1

        # Variables para cargar a la base
        stock_production_lot_ = {'name': None,
                                 'ref': None,
                                 'product_id': None,
                                 'life_date': None,
                                 'removal_date': None,
                                 'alert_date': None, }

        stock_quant_ = {'product_id': None,
                        'qty': None,
                        'lot_id': None,
                        'location_id': None,
                        'in_date': None,
                        'cost': None, }

        # ejemplo:['Ref_Interna', 'Nro_Lote', 'Vencimiento', 'Codigo_AMSJ_Ubicacion', 'Cantidad']
        cantidad_registros = 0
        lineas_archivo = 0
        mensaje = ''
        lista_errores = []

        no_titulo = None

        for i in lineas:

            lineas_archivo += 1

            # Separando los datos del movimiento
            mov = i.split(';')

            # chequeo que no haya titulos

            if len(mov) >= 4:
                no_titulo = mov[0].isdigit()
                # print 'tiene titulos'

            if len(mov) >= 4 and no_titulo:

                if mov[0]:
                    ref_interna = mov[0]
                if mov[1]:
                    nro_lote = mov[1]
                if mov[2]:
                    vencimiento = mov[2]
                if mov[3]:
                    codigo_amsj = mov[3]
                if mov[4]:
                    cantidad = mov[4]

                producto = self.env['product.product'].search([('default_code', '=', ref_interna)])

                if not producto:
                    aux = ('No se encontro el producto ', ref_interna, 'linea ' + str(lineas_archivo), i)
                    lista_errores.append(aux)

                if not codigo_amsj and not self.ubicacion:
                    aux = ('No se encontro el ubicacion ', codigo_amsj, 'linea ' + str(lineas_archivo), i)
                    lista_errores.append(aux)

                # Si existe producto, lote y si hay ubicacion o si hay seleccionada ubicacion
                if producto and nro_lote and (codigo_amsj or self.ubicacion):
                    # print ref_interna

                    prod_id = [x.id for x in producto]
                    p_id = prod_id[0]

                    fecha = datetime.strptime(vencimiento, '%Y-%m-%d')

                    # alerta 60 dias antes
                    alert = fecha - timedelta(days=60)
                    alerta = alert.strftime('%Y-%m-%d')

                    hoy = datetime.now()
                    hoy = hoy.strftime("%Y-%m-%d")

                    # existe_lote=self.env['stock.production.lot'].search([('name','=',nro_lote)])
                    sql = '''select id from stock_production_lot where name = %(nro_lote)s '''
                    self.env.cr.execute(sql, {'nro_lote': nro_lote})
                    existe_lote = self.env.cr.fetchall()

                    var = None
                    saber_id_lot = None

                    if not existe_lote:
                        stock_production_lot_ = {
                            'name': nro_lote,
                            # 'ref':nro_lote,
                            'product_id': p_id,
                            'life_date': vencimiento,
                            'removal_date': vencimiento,
                            'alert_date': alerta, }

                        var = self.env['stock.production.lot'].create(stock_production_lot_)
                        saber_id_lot = var.id

                    if existe_lote:
                        saber_id_lot = existe_lote[0][0]

                    if not saber_id_lot:
                        saber_id_lot = ''

                    ubicacion_final = None

                    if not self.ubicacion:
                        ubic = self.env['stock.location'].search([('codigo_amsj', '=', codigo_amsj)])

                        if ubic:

                            ubicacion_final = [a.id for a in ubic]
                            ubicacion_final = ubicacion_final[0]

                        else:
                            # ubicacion_final=None
                            aux = ('No se encontro la ubicacion ', codigo_amsj, 'linea ' + str(lineas_archivo), i)
                            lista_errores.append(aux)

                    # poner el else.........
                    if self.ubicacion:
                        ubicacion_final = self.ubicacion.id

                    # standard_price
                    costo = self.env['product.product'].browse(p_id)

                    costo_prod = 0

                    if costo.standard_price:
                        costo_prod = costo.standard_price

                    existe_stock_quant = self.env['stock.quant'].search(
                        [('product_id', '=', p_id), ('lot_id', '=', saber_id_lot),
                         ('location_id', '=', ubicacion_final)])

                    # si no existe la ubicacion no guarda registro

                    if existe_stock_quant:
                        cantidad_registros += 1
                        existe_stock_quant.write({'qty': cantidad})



                    # if ubicacion_final != None and not existe_stock_quant:
                    elif ubicacion_final:

                        stock_quant_ = {
                            'product_id': p_id,
                            'qty': cantidad,
                            'lot_id': saber_id_lot,
                            'location_id': ubicacion_final,
                            'in_date': hoy,
                            'cost': costo_prod, }

                        cantidad_registros += 1
                        # print stock_quant_

                        self.env['stock.quant'].create(stock_quant_)

            if len(mov) <= 1:
                registros = str(cantidad_registros)
                aux = "Se cargaron %s registros correctamente" % (registros)

                if len(lista_errores) > 0:
                    mensaje = 'Las siguientes lineas NO se cargaron correctamente:\n'

                    for i in lista_errores:
                        mensaje += ("%s, %s, %s, --> %s \n") % (i[0], i[1], i[2], i[3])

                    self.archivo_para_errores = '- Error en la importacion de Lotes'
                    dato_error = aux + '\n'
                    dato_error += mensaje

                    data_to_save_error = codecs.encode(dato_error, 'utf-8')
                    # data_to_save_error = codecs.decode(dato_error, 'cp1252')
                    data_to_save_error = base64.encodestring(data_to_save_error)

                    self.archivo_errores_contenidos = data_to_save_error


                else:

                    self.mostrar = 'Se importaron %s registros correctamente' % registros






















