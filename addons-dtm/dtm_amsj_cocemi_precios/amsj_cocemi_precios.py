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



class amsj_cocemi_precios(models.TransientModel):
    _name = "amsj.cocemi.precios"

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

            # print 'len',len(mov), 'mov',mov
            
            if len(mov) > 1:
            
                cod_prod = mov[indx_pro]
                # importe = int(mov[indx_importe])
                importe = float(mov[indx_importe].replace(',', '.'))

                if importe > 0:
                    sql = '''UPDATE product_template t
                        set precio_cocemi =  %(importe)s,
                        cocemi = true
                        from product_product p
                        where p.default_code = %(cod_prod)s  and  purchase_ok = True
                        and t.id = p.product_tmpl_id; '''


                    self.env.cr.execute(sql, {'importe':importe,'cod_prod':cod_prod})

            # print 'importe',importe,type(importe),'cod_prod',cod_prod,type(cod_prod)

            # if len(mov)<=1:
        return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            'title': 'Precios de COCEMI',
                            'text': 'Los precios se han cargado correctamente.',
                            'sticky': False
                        }
                    }

        



       




            






        
