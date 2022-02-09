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



class dtm_amsj_importar_stock_critico(models.TransientModel):
    _name = "dtm.amsj.importar.stock.critico"

    file = fields.Binary('Archivo CSV')
    ubicacion = fields.Many2one('stock.location',string='Seleccione la ubicación', required=True)
    
    columna_producto = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                         ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                         ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                         ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                        string="Nro. columna Ref. interna producto", default='0')

   
    # columna_especialidad = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
    #                                     ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
    #                                     ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
    #                                     ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
    #                                    string="Nro. columna codigo de Especialidad", default='1')


    stock_max = fields.Selection([('0', 'A'), ('1', 'B'), ('2', 'C'), ('3', 'D'),
                                        ('4', 'E'), ('5', 'F'), ('6', 'G'), ('7', 'H'), ('8', 'I'),
                                        ('9', 'J'), ('10', 'K'), ('11', 'L'), ('12', 'M'),
                                        ('13', 'N'), ('14', 'O'), ('15', 'P'), ('16', 'Q')],
                                       string="Nro. columna de Stock Máximo", default='2')

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
        
        indx_pro = int(self.columna_producto)
        stock_maximo = int(self.stock_max)

        ubicacion_id=self.ubicacion.id
       
        stock_chequeo=None

        for i in lineas:
            # Separando los datos del movimiento
            mov = i.split(',')

            #chequeo que no haya titulos
     
            if len(mov)==3:    
                stock_chequeo = mov[stock_maximo].isdigit()
                # print 'hay titulos', stock_chequeo 

            
            if len(mov)==3 and stock_chequeo:
            
                cod_prod = mov[indx_pro]
                stc_max = int(mov[stock_maximo])
                
                tipo_de_empaque = self.env['tipo.empaque'].search([('name','=','Caja')])
                
                categoria_id = self.env['categoria'].search([('CodigoAMSJ','=','0')])

      
                prod=self.env['product.product'].search([('default_code','=',cod_prod)])

                prod=[x.product_tmpl_id.id for x in prod]

                p_tempalte=self.env['product.template'].search([('id','in',prod),('categoria_id','=',categoria_id.id),('tipo_de_empaque','=',tipo_de_empaque.id)])

                ids_templates= [r.id for r in p_tempalte]
               
                
                     
                               
                existe=self.env['ubicacion.stockcritico'].search([('product_tmpl_id','in',ids_templates),('ubicacion_id','=',ubicacion_id)])
                existe_ids= [n.id for n in existe]

                if len(existe)>0:


                    for ids in  existe_ids:
                        sql='''UPDATE ubicacion_stockcritico 
                            set stock_critico=%(stock_critico)s
                            where id = %(id)s; '''
                        self.env.cr.execute(sql, {'stock_critico':stc_max, 'id':ids})
                        # print 'aqui actualice!!!!!!!'



                if len(ids_templates)>0 and len(existe_ids) == 0:
                    #en el caso que no tenga cargado categoria_id = fermacia igual lo cargue
                    
                    carga ={
                     'stock_critico':stc_max,
                     'ubicacion_id':ubicacion_id,
                     'product_tmpl_id':prod[0]
                     }
                    
                    # print 'ver carga nueva --> ',carga  
                    self.env['ubicacion.stockcritico'].create(carga)

              


            if len(mov)<=1:
                return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            'title': 'Stock Crítico',
                            'text': 'Se actualizo el Stock crítico',
                            'sticky': False
                        }
                    }

        



       




            






        
