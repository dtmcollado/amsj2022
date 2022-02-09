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

from datetime import date
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError
import logging
import codecs
import base64
from datetime import datetime,timedelta
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

class dtm_saldos_iniciales(models.Model):
    _name = 'dtm.saldos.iniciales'
    name = fields.Text(string='Description')
    producto = fields.Char(string='Código')
    product_id = fields.Many2one('product.product', string='Producto',
                                 ondelete='restrict', index=True)
    cantidad = fields.Integer(string='Cantidad', required=True, default=0)
    precio_puc = fields.Float(u'Precio PUC')
    precio_fifo = fields.Float(u'Precio FIFO')
    fecha_valor = fields.Date('Fecha', default=date.today())


class dtm_amsj_importar_saldos(models.TransientModel):
    _name = "dtm.amsj.importar.saldos"

    file = fields.Binary('Archivo CSV')
    ubicacion = fields.Many2one('stock.location',string='Ubicación')
    bandera = fields.Boolean(string='activador',default=True)
    archivo_nombre = fields.Char('')
    archivo_contenido = fields.Binary(string="Archivo de Ejemplo")
    archivo_para_errores = fields.Char('')
    archivo_errores_contenidos = fields.Binary(string="Error?")
    mostrar = fields.Char('')
    empaque=fields.Many2one('tipo.empaque', string='Tipo de Empaque')


    #creacion de archivo de ejemplo
    @api.onchange('bandera')
    def _onchange_bandera(self):
        self.archivo_nombre='Archivo de ejemplo de importación de Lotes.CSV'
        dato = 'Ref_Interna;Nro_Lote;Vencimiento;Codigo_AMSJ_Ubicacion;Cantidad'+'\n'
        dato += '36704;0000023;2019-12-31;SJMFAR;1' + '\n'
        dato += '36704;0000023;2019-12-31;LIBFAR;5'
        data_to_save = codecs.encode(dato, 'cp1252')
        data_to_save = base64.encodestring(data_to_save)
        self.archivo_contenido=data_to_save
       

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


        #Decodificación y separación en líneas
        lineas = base64.b64decode(self.file)
        lineas = lineas.split('\n')
        #Recibo desde el archivo las siguientes variables
        ref_interna =None







         #ejemplo:['Ref_Interna', 'Nro_Lote', 'Vencimiento', 'Codigo_AMSJ_Ubicacion', 'Cantidad']
        cantidad_registros=0
        lineas_archivo=0
        mensaje=''
        lista_errores=[]
        update_archivos=0
        no_titulo=None
        
        for i in lineas:


            lineas_archivo+=1

            # Separando los datos del movimiento
            mov = i.split(';')


            #chequeo que no haya titulos

            if len(mov)>=4:
                no_titulo = mov[0].isdigit()
                # print 'tiene titulos'


            cantidad = 0
            if len(mov)>=4 and no_titulo:
                # Codigo;Medicamento; Cantidad ; PUC ; PRECIO FIFO
                if mov[0]:
                    ref_interna=mov[0]
                if mov[1]:
                    descripcion=mov[1]
                if mov[2]:
                    cantidad=mov[2]
                if mov[3]:
                    puc = float(mov[3].replace(',', '.'))
                if mov[4]:
                    fifo = float(mov[4].replace(',', '.'))
                #producto=self.env['product.product'].search([('default_code','=',default_code)])
                p_id=None
                producto= None
                sql_resultado=None


                sql_prod = '''select pp.id 
                from product_product pp 
                 join product_template pt on pt.id = pp.product_tmpl_id 
                 where pt.name =  %(default_code)s;
                    '''
                self.env.cr.execute(sql_prod, {'default_code': descripcion})
                sql_resultado = self.env.cr.fetchall()




                if sql_resultado:
                    p_id=sql_resultado[0][0]
                    producto=sql_resultado[0][0]

                    a_out = self.env['dtm.saldos.iniciales'].create({
                        'producto': ref_interna,
                        'product_id': int(p_id),
                        'cantidad': cantidad,
                        'precio_puc': float(puc),
                        'precio_fifo': float(fifo),
                        'name': 'Carga Inicial',
                        'fecha_valor': '2019-12-01'

                    })

                if not producto:
                    aux=('No se encontro el producto con la siguiente referencia interna ',ref_interna, ' linea '+str(lineas_archivo), i)
                    lista_errores.append(aux)


                



            if len(mov)<=1:
                aux=''
                registros = str(cantidad_registros)
                if update_archivos>0:
                    aux="Se cargaron %s registros correctamente, y actualizacion de registros existentes %s" % (registros, int(registros)- int(update_archivos))
                else:
                    aux="Se cargaron %s registros correctamente" % registros

                if len(lista_errores) > 0:
                    mensaje='Las siguientes lineas NO se cargaron correctamente:\n'

                    for i in lista_errores:
                        mensaje+= ("%s, %s, %s, --> %s \n") % (i[0],i[1],i[2],i[3])

                    self.archivo_para_errores='- Error en la importacion de Lotes'
                    dato_error=aux+'\n'
                    dato_error+=mensaje

                    # data_to_save_error = codecs.encode(dato_error, 'utf-8')
                    # data_to_save_error = codecs.decode(dato_error, 'cp1252')
                    # data_to_save_error = base64.encodestring(data_to_save_error)

                    # self.archivo_errores_contenidos=data_to_save_error


                else:
                    self.mostrar = 'Se importaron %s registros correctamente' % registros






















