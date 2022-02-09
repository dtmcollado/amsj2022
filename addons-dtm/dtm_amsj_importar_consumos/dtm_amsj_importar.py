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
import random

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


class dtm_consumos_cobol(models.Model):
    _name = "dtm.amsj.comsumos.importados"

    #     CodGeo	Cantidad	TipoEmpaque	Fecha	Ubicaci�n Origen	Ubicaci�n Destino

    product_id = fields.Many2one('product.template', string='Producto',
                                 ondelete='restrict', index=True
                                 )
    quantity = fields.Integer(string='Cantidad', default=0)
    fecha = fields.Char('Fecha')
    origen = fields.Char('Ubicacion Origen')
    destino = fields.Char('Ubicacion Destino')
    procesado = fields.Boolean(string='Procesado', default=False)


class dtm_consumos_cobol_errores(models.Model):
    _name = "dtm.amsj.comsumos.importados.errores"

    #     CodGeo	Cantidad	TipoEmpaque	Fecha	Ubicaci�n Origen	Ubicaci�n Destino

    cod_geosalud = fields.Char('Codigo GeoSalud')
    quantity = fields.Integer(string='Cantidad', default=0)
    fecha = fields.Char('Fecha')
    origen = fields.Char('Ubicacion Origen')
    destino = fields.Char('Ubicacion Destino')


class dtm_amsj_importar(models.TransientModel):
    _name = "dtm.amsj.importar.consumos"

    file = fields.Binary('Archivo CSV')
    ubicacion = fields.Many2one('stock.location', string='Ubicación')
    bandera = fields.Boolean(string='activador', default=True)
    archivo_nombre = fields.Char('')
    archivo_contenido = fields.Binary(string="Archivo de Ejemplo")
    archivo_para_errores = fields.Char('')
    archivo_errores_contenidos = fields.Binary(string="Error?")
    mostrar = fields.Char('')
    empaque = fields.Many2one('tipo.empaque', string='Tipo de Empaque')

    # creacion de archivo de ejemplo
    @api.onchange('bandera')
    def _onchange_bandera(self):
        self.archivo_nombre = 'Archivo de ejemplo de importación de consumos.CSV'
        dato = 'Ref_Interna;Nro_Lote;Vencimiento;Codigo_AMSJ_Ubicacion;Cantidad' + '\n'
        dato += '36704;0000023;2019-12-31;SJMFAR;1' + '\n'
        dato += '36704;0000023;2019-12-31;LIBFAR;5'
        data_to_save = codecs.encode(dato, 'cp1252')
        data_to_save = base64.encodestring(data_to_save)
        self.archivo_contenido = data_to_save

    @api.multi
    def generar(self):
        self.env.cr.execute(
            """
              SELECT product_id as product_tmpl_id, fecha, 
        quantity, l.id as origen_id , l2.id as destino_id , a.int_type_id , pt.uom_id , p.id as product_id , dtm_amsj_comsumos_importados.id as id
      FROM dtm_amsj_comsumos_importados
  INNER JOIN stock_location l ON l.codigo_amsj = origen 
  INNER JOIN stock_location l2 ON l2.codigo_amsj = destino
  INNER JOIN stock_warehouse a ON a.id = l.almacen_id
  INNER JOIN product_template pt ON pt.id = product_id
  INNER JOIN product_product p ON p.product_tmpl_id = pt.id
  where coalesce(procesado,false) = false 
  order by l.id , l2.id , fecha
            """
        )

        resultado = self.env.cr.fetchall()
        primero = True
        origen_ant = ''
        destino_ant = ''
        fecha_ant = ''
        picking_out = False
        total = 0

        for tupla in resultado:
            prod_template_id = tupla[0]
            fecha = tupla[1]
            cant = tupla[2]
            origen_id = tupla[3]
            destino_id = tupla[4]
            out_type = tupla[5]
            prod_id = tupla[7]
            xId = tupla[8]

            total += 1
            number = random.randint(1, 9999999)

            if primero:
                origen_ant = tupla[3]
                destino_ant = tupla[4]
                fecha_ant = tupla[1]

                picking_out = self.env['stock.picking'].create({
                    "location_id": int(origen_id),
                    'location_dest_id': int(destino_id),
                    'picking_type_id': out_type,
                    'sector_id': int(17),
                    'state': 'done',
                    'date_done': fecha,
                    'date': fecha,
                    'origin': 'Migrado ' + str(number),

                })

                # self.env['stock.move'].create({
                #     'name': 'Consumo migrado',
                #     'product_id': prod_id,
                #     'product_uom_qty': cant,
                #     'product_uom': tupla[6],
                #     'picking_id': picking_out.id,
                #     'picking_type_id': out_type,
                #     'location_id': origen_id,
                #     'state': 'done',
                #     'date': fecha,
                #     'location_dest_id': destino_id,
                # })

                # INSERT
                # INTO
                # "stock_move"("id", "origin", "product_uos_qty", "product_uom", "product_uom_qty", "product_qty",
                #              "price_unit", "procure_method", "product_uos", "location_id", "picking_type_id",
                #              "partner_id", "company_id", "priority", "state", "product_packaging", "date_expected",
                #              "partially_available", "propagate", "date", "product_id",
                #              "name", "invoice_state", "location_dest_id", "group_id", "picking_id", "create_uid",
                #              "write_uid", "create_date", "write_date")
                # VALUES(_stock_move_id, CONCAT(_location_origin_amsj, '\\OUT\\', _stock_picking_id::character
                # varying), _product_qty, _product_uom, _product_qty, _product_qty, _product_cost, 'make_to_stock', NULL, _location_origin_id, _picking_type_id,
                #           NULL, 1, '1', 'done', NULL, (now() at time zone 'UYT'),
                #           false, true, (now()
                #                         at time zone 'UYT'), _product_id, _product_name, 'none', _location_destination_id, NULL, _stock_picking_id, 1, 1, (
                #               now() at time zone 'UYT'), (now() at time zone 'UYT'));

                sql_stock = '''INSERT INTO stock_move(name,product_id,product_uom_qty,product_uom,picking_id,picking_type_id,
                                   location_id,state,date,location_dest_id,company_id,
                                   date_expected,procure_method,invoice_state,create_date,product_qty) 
                                VALUES(%(x_name)s,
                                       %(x_product_id)s,
                                        %(x_product_uom_qty)s,
                                        %(x_product_uom)s,
                                        %(x_picking_id)s,
                                        %(x_picking_type_id)s,
                                        %(x_location_id)s,
                                        %(x_state)s,
                                         %(x_date)s,
                                          %(x_location_dest_id)s,1,%(x_date)s, 
                                          'make_to_stock','none',%(x_date)s,
                                          %(x_product_uom_qty)s
                                        );'''

                parametros = {
                    'x_name': 'Consumo migrado 1',
                    'x_product_id': prod_id,
                    'x_product_uom_qty': cant,
                    'x_product_uom': tupla[6],
                    'x_picking_id': picking_out.id,
                    'x_picking_type_id': out_type,
                    'x_location_id': origen_id,
                    'x_state': 'done',
                    'x_date': fecha,
                    'x_location_dest_id': destino_id,
                }

                # create_date
                # product_qty

                self.env.cr.execute(sql_stock, parametros)

                primero = False

            else:
                if (origen_id == origen_ant) and (destino_id == destino_ant) and (fecha == fecha_ant):
                    sql_stock = '''INSERT INTO stock_move(name,product_id,product_uom_qty,product_uom,picking_id,picking_type_id,
                                                       location_id,state,date,location_dest_id,company_id,
                                                       date_expected,procure_method,invoice_state,create_date,product_qty) 
                                                    VALUES(%(x_name)s,
                                                           %(x_product_id)s,
                                                            %(x_product_uom_qty)s,
                                                            %(x_product_uom)s,
                                                            %(x_picking_id)s,
                                                            %(x_picking_type_id)s,
                                                            %(x_location_id)s,
                                                            %(x_state)s,
                                                             %(x_date)s,
                                                              %(x_location_dest_id)s,1,%(x_date)s, 
                                                              'make_to_stock','none',%(x_date)s,
                                                              %(x_product_uom_qty)s
                                                            );'''

                    parametros = {
                        'x_name': 'Consumo migrado 1',
                        'x_product_id': prod_id,
                        'x_product_uom_qty': cant,
                        'x_product_uom': tupla[6],
                        'x_picking_id': picking_out.id,
                        'x_picking_type_id': out_type,
                        'x_location_id': origen_id,
                        'x_state': 'done',
                        'x_date': fecha,
                        'x_location_dest_id': destino_id,
                    }

                    self.env.cr.execute(sql_stock, parametros)
                    # creo move
                else:
                    # creo picking
                    picking_out = self.env['stock.picking'].create({
                        "location_id": int(origen_id),
                        'location_dest_id': int(destino_id),
                        'picking_type_id': out_type,
                        'sector_id': int(17),
                        'state': 'done',
                        'date_done': fecha,
                        'date': fecha,
                        'origin': 'Migrado ' + str(number),

                    })

                    sql_stock = '''INSERT INTO stock_move(name,product_id,product_uom_qty,product_uom,picking_id,picking_type_id,
                                                       location_id,state,date,location_dest_id,company_id,
                                                       date_expected,procure_method,invoice_state,create_date,product_qty) 
                                                    VALUES(%(x_name)s,
                                                           %(x_product_id)s,
                                                            %(x_product_uom_qty)s,
                                                            %(x_product_uom)s,
                                                            %(x_picking_id)s,
                                                            %(x_picking_type_id)s,
                                                            %(x_location_id)s,
                                                            %(x_state)s,
                                                             %(x_date)s,
                                                              %(x_location_dest_id)s,1,%(x_date)s, 
                                                              'make_to_stock','none',%(x_date)s,
                                                              %(x_product_uom_qty)s
                                                            );'''

                    parametros = {
                        'x_name': 'Consumo migrado 1',
                        'x_product_id': prod_id,
                        'x_product_uom_qty': cant,
                        'x_product_uom': tupla[6],
                        'x_picking_id': picking_out.id,
                        'x_picking_type_id': out_type,
                        'x_location_id': origen_id,
                        'x_state': 'done',
                        'x_date': fecha,
                        'x_location_dest_id': destino_id,
                    }

                    self.env.cr.execute(sql_stock, parametros)

                    origen_ant = tupla[3]
                    destino_ant = tupla[4]
                    fecha_ant = tupla[1]

            sql_update = """
                            UPDATE dtm_amsj_comsumos_importados
                            SET  procesado=True
                            WHERE id = %(p_id)s;
                        """

            parametros = {
                'p_id': xId,
            }

            self.env.cr.execute(sql_update, parametros)

    @api.multi
    def import_csv_consumos(self):
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

        # ejemplo:['Ref_Interna', 'Nro_Lote', 'Vencimiento', 'Codigo_AMSJ_Ubicacion', 'Cantidad']
        cantidad_registros = 0
        lineas_archivo = 0
        mensaje = ''
        lista_errores = []
        update_archivos = 0
        no_titulo = None

        for i in lineas:
            # CodGeo;Cantidad;TipoEmpaque;Fecha;Ubicacion Origen;Ubicacion Destino
            lineas_archivo += 1

            # Separando los datos del movimiento
            mov = i.split(';')

            if mov[0]:
                CodGeo = mov[0]

                producto = self.env['product.template'].search(
                    [('codigo_geosalud', '=', CodGeo), ('tipo_de_empaque.name', '=', 'Caja')], limit=1)
                if producto:
                    if mov[1]:
                        Cantidad = mov[1]
                    if mov[3]:
                        Fecha = mov[3]
                    if mov[4]:
                        origen = mov[4]
                    if mov[5]:
                        destino = mov[5]

                    # importado = self.env['dtm.amsj.comsumos.importados'].create({
                    #     'product_id': producto.id,
                    #     'quantity': Cantidad,
                    #     'fecha': Fecha,
                    #     'origen': origen.strip(),
                    #     'destino': destino.strip()
                    # })

                    sql_stock = '''INSERT INTO  dtm_amsj_comsumos_importados(
                          product_id, fecha, destino,
                          origen, quantity, procesado)
                                                    VALUES(%(x_1)s,
                                                           %(x_2)s,
                                                            %(x_3)s,
                                                            %(x_4)s,
                                                            %(x_5)s,
                                                            %(x_6)s
                                                            );'''

                    parametros = {
                        'x_1': producto.id,
                        'x_2': Fecha,
                        'x_3': destino.strip(),
                        'x_4': origen.strip(),
                        'x_5': Cantidad,
                        'x_6': False,
                    }

                    # create_date
                    # product_qty

                    self.env.cr.execute(sql_stock, parametros)

                # else:
                #     x = 'error'
                #
                #     err = self.env['dtm.amsj.comsumos.importados.errores'].create({
                #         'cod_geosalud': mov[0],
                #         'quantity': mov[1],
                #         'fecha': mov[3],
                #         'origen': mov[4],
                #         'destino': mov[5]})

        self.mostrar = 'Se importaron %s registros correctamente'

    @api.multi
    def import_csv_tipo(self):
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

        # ejemplo:['Ref_Interna', 'Nro_Lote', 'Vencimiento', 'Codigo_AMSJ_Ubicacion', 'Cantidad']
        cantidad_registros = 0
        lineas_archivo = 0
        mensaje = ''
        lista_errores = []
        update_archivos = 0
        no_titulo = None

        for i in lineas:
            # CodGeo;Cantidad;TipoEmpaque;Fecha;Ubicacion Origen;Ubicacion Destino
            lineas_archivo += 1

            # Separando los datos del movimiento
            mov = i.split(';')

            if mov[1]:

                CodMsp = mov[1]
                producto = self.env['product.template'].search(
                    [('default_code', '=', CodMsp), ('tipo_de_empaque.name', '=', 'Caja')], limit=1)

                # LICITACION 4  o MENSUAL 3

                if mov[0] == 'MENSUAL':
                    actualiza = 'UPDATE product_template SET forma_de_compra = 3 WHERE id = ' + str(producto.id)


                else:
                    actualiza = 'UPDATE product_template SET forma_de_compra = 4 WHERE id = ' + str(producto.id)

                if producto:
                    x = 1
                    print lineas_archivo
                    salida = self.env.cr.execute(actualiza)
                    print salida
        self.mostrar = 'Se importaron %s registros correctamente'

    @api.multi
    def import_csv_consumos_nuevos(self):
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

        # ejemplo:['Ref_Interna', 'Nro_Lote', 'Vencimiento', 'Codigo_AMSJ_Ubicacion', 'Cantidad']
        cantidad_registros = 0
        lineas_archivo = 0
        mensaje = ''
        lista_errores = []
        update_archivos = 0
        no_titulo = None

        fecha1 = '2019-08-15'
        indice1 = 1

        fecha2 = '2019-09-15'
        indice2 = 2

        fecha3 = '2019-10-15'
        indice3 = 3

        fecha4 = '2019-11-15'
        indice4 = 4

        fecha5 = '2019-12-15'
        indice5 = 5

        # ===========================
        fecha6 = '2020-01-15'
        indice6 = 6

        fecha7 = '2020-02-15'
        indice7 = 7

        fecha8 = '2020-03-15'
        indice8 = 8

        fecha9 = '2020-04-15'
        indice9 = 9

        fecha10 = '2020-05-15'
        indice10 = 10

        fecha11 = '2020-06-15'
        indice11 = 11

        fecha12 = '2020-07-15'
        indice12 = 12

        # 1 ago , 2 set , 3 oct , 4 nov , 5 dic , 6 ene , 7 feb ,
        # 8 mar , 9 abril , 10 mayo , 11 junio , 12 julio

        picking_out = self.env['stock.picking'].create({
            'location_id': int(551),
            'location_dest_id': int(781),
            'picking_type_id': 153,
            'sector_id': int(17),
            'state': 'done',
            'date_done': '2019-01-01',
            'date': '2019-01-01',
            'origin': 'Migrado ok 19-20',

        })

        for i in lineas:
            # CodGeo;Cantidad;TipoEmpaque;Fecha;Ubicacion Origen;Ubicacion Destino
            lineas_archivo += 1

            # Separando los datos del movimiento
            mov = i.split(';')

            if mov[0]:

                CodMsp = mov[0]
                producto = self.env['product.template'].search(
                    [('default_code', '=', CodMsp), ('tipo_de_empaque.name', '=', 'Caja')], limit=1)

                producto_producto = self.env['product.product'].search([('product_tmpl_id', '=', producto.id)], limit=1)

                if producto:

                    a = 1
                    while a < 13:
                        cantidad = int(mov[a])
                        if cantidad > 0:
                            sql_stock = '''INSERT INTO stock_move(name,product_id,product_uom_qty,product_uom,picking_id,picking_type_id,
                                                                                       location_id,state,date,location_dest_id,company_id,
                                                                                       date_expected,procure_method,invoice_state,create_date,product_qty)
                                                                                    VALUES(%(x_name)s,
                                                                                           %(x_product_id)s,
                                                                                            %(x_product_uom_qty)s,
                                                                                            %(x_product_uom)s,
                                                                                            %(x_picking_id)s,
                                                                                            %(x_picking_type_id)s,
                                                                                            %(x_location_id)s,
                                                                                            %(x_state)s,
                                                                                             %(x_date)s,
                                                                                              %(x_location_dest_id)s,1,%(x_date)s,
                                                                                              'make_to_stock','none',%(x_date)s,
                                                                                              %(x_product_uom_qty)s
                                               
                                                                                            );'''

                            if a == 1:
                                fecha = fecha1
                            if a == 2:
                                fecha = fecha2
                            if a == 3:
                                fecha = fecha3
                            if a == 4:
                                fecha = fecha4
                            if a == 5:
                                fecha = fecha5
                            if a == 6:
                                fecha = fecha6
                            if a == 7:
                                fecha = fecha7
                            if a == 8:
                                fecha = fecha8
                            if a == 9:
                                fecha = fecha9
                            if a == 10:
                                fecha = fecha10
                            if a == 11:
                                fecha = fecha11
                            if a == 12:
                                fecha = fecha12

                            parametros = {
                                'x_name': 'Consumo migrado mensual 19-20',
                                'x_product_id': producto_producto.id,
                                'x_product_uom_qty': cantidad,
                                'x_product_uom': producto.uom_id.id,
                                'x_picking_id': picking_out.id,
                                'x_picking_type_id': 153,
                                'x_location_id': 551,
                                'x_state': 'done',
                                'x_date': fecha,
                                'x_location_dest_id': 781,
                            }

                            self.env.cr.execute(sql_stock, parametros)
                            print lineas_archivo
                        a += 1

        #                 ///////////////////////////////////////////

        self.mostrar = 'Se importaron %s registros correctamente'
