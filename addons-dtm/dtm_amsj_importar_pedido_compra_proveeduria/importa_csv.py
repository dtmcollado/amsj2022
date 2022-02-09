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
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
import logging
import codecs

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')

# Aclaración: Comenté el siguiente código porque no parece
# que estemos usando xlwt para nada
# try:
#     import xlwt
# except ImportError:
#     _logger.debug('Cannot `import xlwt`.')

try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')

CODIGO_PROVEEDURIA = '1'

class gen_central_proveeduria(models.TransientModel):
    _name = "gen.central.proveeduria"

    file = fields.Binary('Archivo CSV')
    name = fields.Char(string='Referencia', index=True, required=True)
    date = fields.Date(string='Fecha',
                       index=True, copy=False, default=date.today(), required=True)

    bandera = fields.Boolean(string='activador',default=True)
    archivo_nombre = fields.Char('')
    archivo_contenido = fields.Binary(string="Archivo de Ejemplo")

    archivo_para_errores = fields.Char('')
    archivo_errores_contenidos = fields.Binary(string="Error?")
    mostrar = fields.Char('')





    columna_producto = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                         ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                         ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                         ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                        string="Nro. columna Ref. interna producto", default='0')

    columna_cantidad = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                         ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                         ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                         ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                        string="Nro. columna Cantidad", default='1')

    columna_importe = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                        ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                        ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                        ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                       string="Nro. columna Importe Unitario", default='2')

    #creacion de archivo de ejemplo
    @api.onchange('bandera')
    def _onchange_bandera(self):
        self.archivo_nombre=u'Archivo de ejemplo Compras Importadas Proveeduria.CSV'
        dato = 'Referencia_interna;Cantidad;Importe_Unitario'+'\n'
        dato += '671680;120;155' + '\n'
        dato += '34025;178;233'
        data_to_save = codecs.encode(dato, 'cp1252')
        data_to_save = base64.encodestring(data_to_save)
        self.archivo_contenido=data_to_save



    # aux=(u'No se encontró la ubicación ',codigo_amsj, u' - línea Nro'+str(linea), i)
    # lista_errores.append(aux)

    @api.multi
    def import_csv(self):
        data = base64.b64decode(self.file)
        file_input = cStringIO.StringIO(data)
        file_input.seek(0)
        reader_info = []
        reader = csv.reader(file_input, delimiter=';')
        lista_errores=[]

        try:
            reader_info.extend(reader)

        except Exception:
            raise exceptions.Warning(_("Archivo con formato invalido"))

        cabezal = self.env['dtm.amsj.compras.importadas.proveeduria'].create({
            'name': self.name,
            'date': self.date
        })
        total_registros = range(len(reader_info))

        mov = 0
        linea=0

        no_titulo = None
        for i in range(len(reader_info)):
            field = map(str, reader_info[i])

            cod_interno=None
            cantidad = None
            precio_uni = None
            linea+=1

            if len(field)<=2 and len(field)>0:
                aux=(u'La siguiente linea le faltan campos',' ', u' - línea Nro '+str(linea), field)
                lista_errores.append(aux)


            if field and len(field)>2:

                # values = dict(zip(keys, field))

                indx_pro = int(self.columna_producto)
                indx_cantidad = int(self.columna_cantidad)
                indx_importe = int(self.columna_importe)

                if len(field)>=1:
                    no_titulo = field[indx_cantidad].isdigit()


                if field[indx_pro] and no_titulo:
                    cod_interno = field[indx_pro]
                if field[indx_cantidad] and no_titulo:
                    cantidad = field[indx_cantidad]
                if field[indx_importe] and no_titulo:
                    precio_uni = field[indx_importe]

                product_ids = None

                if not cod_interno and no_titulo:
                    aux=(u'Error en el Código Interno ',field[indx_pro], u' - línea Nro '+str(linea), field)
                    lista_errores.append(aux)
                if not cantidad and no_titulo:
                    aux=(u'Error en la Cantidad ',field[indx_cantidad], u' - línea Nro '+str(linea), field)
                    lista_errores.append(aux)
                if not precio_uni and no_titulo:
                    aux=(u'Error en el Precio unitario ',field[indx_importe], u' - línea Nro '+str(linea), field)
                    lista_errores.append(aux)

                cod_interno_prov = True

                if cod_interno:
                    # Buscar producto
                    product = self.env['product.template'].search([
                        ('default_code', '=', cod_interno),
                        ('purchase_ok', '=', 'True'),
                    ], limit=1)
                    product_ids = self.env['product.template'].search([
                        ('default_code', '=', cod_interno),
                        ('purchase_ok', '=', 'True'),
                        ('categoria_id', '=',19),
                    ], limit=1)
                    if not product_ids and product:
                        aux=(u'El siguiente Producto no es administrado por Proveeduría ', cod_interno , u' - línea Nro' + str(linea), field)
                        lista_errores.append(aux)
                        cod_interno_prov = False

                    if not product_ids and not product:
                        aux=(u'No se encontró el Producto con el código ', cod_interno , u' - línea Nro'+str(linea), field)
                        lista_errores.append(aux)
                        cod_interno_prov = False



                if cod_interno and cod_interno_prov and cantidad and precio_uni:
                    # Buscar producto
                    product_ids = self.env['product.template'].search([
                        ('default_code', '=', cod_interno),
                        ('purchase_ok', '=', 'True'),
                        ('categoria_id', '=',19),
                    ], limit=1)



                    for pro in product_ids:

                        if pro.purchase_ok and pro.categoria_id.CodigoAMSJ == CODIGO_PROVEEDURIA:

                            producto_producto = self.env['product.product'].search([('product_tmpl_id', '=', pro.id)],limit=1)

                            try:
                                if cantidad:
                                    cant = int(cantidad.replace(".", ""))

                                else:
                                    cant = 0

                            except ValueError:
                                cant = 0

                            # *******************
                            try:
                                if precio_uni != False:
                                    precio_uni = float(precio_uni.replace(',', '.'))

                                else:
                                    precio_uni = 0

                            except (ValueError, AttributeError):
                                precio_uni = 0

                            archivo_correcto=True
                            # V A L I D A C I O N E S ! ! ! ! !
                            proveedor_id = self.env['res.partner'].search([('id', '=', pro.seller_ids.name.id)])

                            if not proveedor_id.codigoAMSJ:
                                aux=(u'Al siguiente Proveedor le falta el código AMSJ ', proveedor_id.name, u' - línea Nro '+str(linea), field)
                                lista_errores.append(aux)
                                archivo_correcto = False

                            if not proveedor_id.codigoAMSJ[:3] == 'med' or proveedor_id.codigoAMSJ[:3] == 'com':
                                aux=(u'En el Proveedor no es correcto el código AMSJ ', proveedor_id.name, u' - línea Nro '+str(linea), field)
                                lista_errores.append(aux)
                                archivo_correcto = False

                            #import ipdb; ipdb.set_trace()  # breakpoint 7f2548f4 //
                            if cabezal and product_ids and archivo_correcto:

                                if precio_uni > 0:
                                    self.env['dtm.amsj.compras.importadas.lineas.proveeduria'].create({
                                        'name': cod_interno,
                                        'quantity': cant,
                                        'precio_unitario': precio_uni,
                                        'partner_id': pro.seller_ids.name.id,
                                        'product_id': producto_producto.id,
                                        'importado_id': cabezal.id
                                    })
                                    mov+=1
                                else:
                                    self.env['dtm.amsj.compras.importadas.lineas.proveeduria'].create({
                                        'name': cod_interno,
                                        'quantity': cant,
                                        'precio_unitario': 0,
                                        'partner_id': pro.seller_ids.name.id,
                                        'product_id': producto_producto.id,
                                        'importado_id': cabezal.id
                                    })
                                    mov+=1

                            # else:
                            #     self.env['dtm.amsj.compras.importadas.lineas.proveeduria'].create({
                            #         'name': cod_interno,
                            #         'quantity': cant,
                            #         'precio_unitario': precio_uni,
                            #         'importado_id': cabezal.id
                            #     })
                            #     mov+=1




        if len(str(mov))<=1:
            registros=str(mov)
            aux="Se importaron exitosamente %s registros" % (registros)


            if len(lista_errores) > 0:
                mensaje=u'No se importaron las siguientes líneas:\n'
                for i in lista_errores:
                    mensaje+= ("%s, %s, %s,--> %s \n") % (i[0],i[1],i[2],i[3])


                self.archivo_para_errores=u'- Error en la importación de Compras de Proveeduria'
                dato_error=aux+'\n'
                dato_error+=mensaje

                data_to_save_error = codecs.encode(dato_error, 'utf-8')
                # data_to_save_error = codecs.decode(dato_error, 'cp1252')
                data_to_save_error = base64.encodestring(data_to_save_error)

                self.archivo_errores_contenidos=data_to_save_error


            else:

                self.mostrar='Se importaron %s registros correctamente' % registros




        # return {
        #     'target': cabezal.id,
        #     'name': _('Compra'),
        #     'view_type': 'form',
        #     'view_mode': 'tree,form',
        #     'res_model': 'dtm.amsj.compras.importadas.proveeduria',
        #     'view_id': False,
        #     'type': 'ir.actions.act_window',
        # }
