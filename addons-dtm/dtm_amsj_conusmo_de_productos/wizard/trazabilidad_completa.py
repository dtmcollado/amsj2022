# -*- encoding: utf-8 -*-

import base64
import xlwt
from cStringIO import StringIO
from datetime import date
from xlsxwriter.workbook import Workbook
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

from dateutil.relativedelta import relativedelta
import datetime
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from ..library import operaciones as report_ops
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class trazabilidad_completa(models.TransientModel):
    _name = "wizard.trazabilidad_completa"

    fecha_inicial = fields.Date('Fecha desde', default=date.today().replace(day=1))
    fecha_final = fields.Date('Fecha hasta', default=date.today())
    warehouse_id = fields.Many2one(comodel_name='stock.warehouse',string='Almacen',required=True)
    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")

    @api.multi
    def action_excel_report(self):
        self.ensure_one()
        final = date(*map(int, self.fecha_final.split("-")))
        inicial = final - relativedelta(months=11)

        # Creo el libro Excel
        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)

        # Estilos
        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        header = easyxf('font: name Calibri, bold True; alignment: horizontal center;')
        """
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')
        """

        title_big = easyxf(
            'font: name Arial, bold True; alignment: horizontal center;font:height 300;pattern: pattern solid, fore_colour pale_blue;')
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')

        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        header_left = easyxf('font: name Calibri, bold True; alignment: horizontal left;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')

        texto = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')
        title_ice_blue = easyxf(
            'pattern: pattern solid, fore_colour ice_blue;font: bold 1 ,height 230; alignment: horizontal center')
        lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
        lineas_estilo_gris = easyxf(
            'pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
        lineas_estilo_num = easyxf('font: name Calibri; alignment: horizontal right',
                                   num_format_str='#.##0,0;-#.##0,0;')
        # num_format_str='#.##0,0;-#.##0,0;')
        lineas_estilo_gris_num = easyxf(
            'pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;',
            num_format_str='#,##0.00;-#,##0.00;')
        #  #.##0,00

        lineas_estilo_num_int = easyxf('font: name Calibri; alignment: horizontal right',
                                       num_format_str='0')

        fila = 0

        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        ws.write_merge(fila, fila, 3, 7, "Planilla Trazabilidad Completa", title_big)

        # ws.write(1, 0, u"Filtros", header_left)
        ws.write(2, 0, u"Rango de Fechas", header_left)
        ws.write(2, 1, u'Desde ' + self.fecha_inicial, fecha)
        ws.write(2, 2, u'Hasta ' + self.fecha_final, fecha)
        ws.write(2, 3, u'Almacen ' + self.warehouse_id.name)
        fila += 10

        # **************


        ws.write(fila, 0, u"Producto", title_ice_blue)
        ws.write(fila, 1, u"Stock Inicial", title_ice_blue)
        ws.write(fila, 2, u"Entradas", title_ice_blue)
        ws.write(fila, 3, u"Salidas", title_ice_blue)
        ws.write(fila, 4, u"Stock Final", title_ice_blue)
        ws.write(fila, 5, u"Tipo", title_ice_blue)
        fila += 1
        product_ids = self.env['product.template'].search([('tipo_id','in',(19,20))])
        if product_ids:
            for producto in product_ids:
                product_id = self.env['product.product'].search([('product_tmpl_id','=', producto.id)],limit=1)
                if product_id:
                        # Escribo el titulo
                    cantidad_entradas=float()
                    cantidad_salidas = float()
                    cantidad_compras=float()
                    stock_final=float()
                    stock_inicial=float()
                    location_dest_ids =[]
                    #consulta_compras = """select
                        #            SUM(product_uom_qty)
                         #           FROM stock_move where state = 'done' and location_id = 8 and location_dest_id = %(location)s and date_expected >= %(fecha_inicial)s and date_expected <= %(fecha_final)s and product_id = %(product_id)s and purchase_line_id is not null"""

                    #self.env.cr.execute(consulta_compras,
                      #                  {'fecha_inicial': self.fecha_inicial,
                       #                  'fecha_final': self.fecha_final,
                       #                  'product_id': product_id.id,
                       #                  'location': self.warehouse_id.wh_input_stock_loc_id.id
                       #                  })

                    #resultado = self.env.cr.fetchall()
                    #for dato in resultado:
                    #   if dato[0] > 0:
                    #      cantidad_compras = dato[0]
                    ubicaciones_entrada_ids = []
                    ubicaciones_salidas_ids = []
                    ubicaciones_stock_ids = []

                    consulta_ubicacion_entrada = """select id from stock_location where usage = 'internal' and almacen_id = %(almacen_id)s and principal_del_expendio"""
                    self.env.cr.execute(consulta_ubicacion_entrada,
                                            {'almacen_id': self.warehouse_id.id})
                    resultado = self.env.cr.fetchall()
                    for dato in resultado:
                        ubicaciones_entrada_ids.append(dato[0])

                    #  cesar
                        consulta_ubicacion_stock = """select id from stock_location where usage = 'internal' and almacen_id = %(almacen_id)s"""
                        self.env.cr.execute(consulta_ubicacion_stock,
                                            {'almacen_id': self.warehouse_id.id})
                        resultado = self.env.cr.fetchall()
                        for dato in resultado:
                            ubicaciones_stock_ids.append(dato[0])

                        #  cesar
                    consulta_ubicacion_salidas = """select id from stock_location where usage = 'customer' and almacen_id = %(almacen_id)s"""
                    self.env.cr.execute(consulta_ubicacion_salidas,
                                            {'almacen_id': self.warehouse_id.id})
                    resultado = self.env.cr.fetchall()
                    for dato in resultado:
                        ubicaciones_salidas_ids.append(dato[0])

                    consulta_entradas = """select
                                        SUM(sm.product_uom_qty)
                                        FROM stock_move sm
                                        where 
                                         sm.state = 'done' 
                                         and sm.location_id NOT IN (4,5)
                                         and sm.location_dest_id in %(ubicaciones_entrada_ids)s 
                                         and sm.date > %(fecha_inicial)s and sm.date <= %(fecha_final)s and sm.product_id = %(product_id)s"""

                    self.env.cr.execute(consulta_entradas,
                                            {'fecha_inicial': self.fecha_inicial,
                                             'fecha_final': self.fecha_final,
                                             'product_id': product_id.id,
                                             'ubicaciones_entrada_ids': tuple(ubicaciones_entrada_ids),
                                             #'ubicaciones_salidas_ids': tuple(ubicaciones_salidas_ids) + tuple(ubicaciones_entrada_ids)
                                             })

                    resultado = self.env.cr.fetchall()
                    for dato in resultado:
                        if dato[0] > 0:
                            cantidad_entradas = dato[0]

                    cantidad_entradas = cantidad_entradas + cantidad_compras
                    consulta_salidas = """select
                                    SUM(sm.product_uom_qty)
                                    FROM stock_move sm
                                    where sm.state = 'done' and
                                       sm.location_dest_id NOT IN (4,5) and
                                       sm.location_dest_id in %(ubicaciones_salidas_ids)s 
                                      and sm.date > %(fecha_inicial)s and sm.date <= %(fecha_final)s 
                                      and sm.product_id = %(product_id)s"""

                    self.env.cr.execute(consulta_salidas,
                                        {'fecha_inicial': self.fecha_inicial,
                                         'fecha_final': self.fecha_final,
                                         'product_id': product_id.id,
                                         'ubicaciones_entrada_ids': tuple(ubicaciones_entrada_ids),
                                         'ubicaciones_salidas_ids': tuple(ubicaciones_salidas_ids)
                                         })
                    resultado = self.env.cr.fetchall()
                    for dato in resultado:
                        if dato[0] > 0:
                            cantidad_salidas = dato[0]


                    for ubicacion in ubicaciones_stock_ids:
                        self.env.cr.execute('select qty from sp_stock_history_date_detail_sin45(%s,%s) where product_id = %s',(ubicacion, self.fecha_inicial,product_id.id))
                        resultados = self.env.cr.fetchall()
                        for resultado in resultados:
                            stock_inicial += resultado[0]

                    if stock_inicial < 0:
                        stock_inicial = 0
                    stock_final = (stock_inicial + cantidad_entradas) - cantidad_salidas
                    ws.write(fila, 0, product_id.name)
                    ws.write(fila, 1, stock_inicial)
                    ws.write(fila, 2, cantidad_entradas)
                    ws.write(fila, 3, cantidad_salidas)
                    ws.write(fila, 4, stock_final)
                    ws.write(fila, 5, product_id.product_tmpl_id.tipo_id.name)
                    fila += 1
        # Escribo una linea por producto encontrado
        # La última columna es para el color

        fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 45,
            1: 20,
            2: 20,
            3: 20,
            4: 30,
            5: 30,
            6: 35,
            7: 30,
            8: 20,
            9: 20,
            10: 20,
            11: 15,
            12: 25,
            13: 25,
            14: 35,
            15: 30,
            16: 30,
            17: 20,
            18: 25,
            19: 25,
            20: 25,
            21: 25,
            22: 25,
            23: 40,
            24: 40,
            25: 40,
            26: 45,
            27: 45,
            28: 45,
            29: 45,
            30: 45,
            31: 45,
            32: 45,
            33: 50,
        }

        for col in range(0, 33):
            ws.col(col).width = anchos.get(col, 7) * 367

        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Trazabilidad_compelta.xls",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.trazabilidad_completa&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }
