# -*- coding: utf-8 -*-
import os
import base64

import xlwt
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

import datetime, time
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO


class dtm_amsj_export_fifo(models.TransientModel):
    _name = "dtm.amsj.stock.tipo"

    ubicacion = fields.Many2one('stock.location', string='Ubicación', domain="[('usage','=','internal')]")

    binario = fields.Binary(string='guardo_archivo')
    archivo_nombre = fields.Char(string='')
    product_id = fields.Many2one('product.product', string='Producto', ondelete='restrict', index=True)
    category_id = fields.Many2one(comodel_name='product.category', string=u'Categoría')
    tipo_id = fields.Many2one(comodel_name='tipo', string=u'Tipo')

    def _get_fecha_fin(self):
        sql = '''SELECT max(date) as fecha from stock_inventory si
                 where si.inv_por_contabilidad = true
                '''

        self.env.cr.execute(sql)
        sql_result = self.env.cr.fetchall()
        if sql_result:
            sql_result = sql_result[0][0]
            if sql_result is None:
                return False
            else:
                dt = datetime.datetime.strptime(sql_result, '%Y-%m-%d %H:%M:%S')
                return dt.date()

    def _get_fecha_inicio(self):

        sql = '''SELECT extract(YEAR FROM max(date)) as anio from stock_inventory si
                 where si.inv_por_contabilidad = true
                '''
        anio = None
        self.env.cr.execute(sql)
        sql_result = self.env.cr.fetchall()
        if sql_result:
            sql_result = sql_result[0][0]
            if sql_result is None:
                pass
            else:
                anio = sql_result

        sql = '''SELECT min("date") as fecha from stock_inventory si
                    where EXTRACT(YEAR FROM "date") = %(anio)s
                    AND si.inv_por_contabilidad = true
                '''

        self.env.cr.execute(sql, {'anio': anio})
        sql_result = self.env.cr.fetchall()
        if sql_result:
            sql_result = sql_result[0][0]
            if sql_result is None:
                return False
            else:
                dt = datetime.datetime.strptime(sql_result, '%Y-%m-%d %H:%M:%S')
                return dt.date()

    fecha_inicial = fields.Date('Fecha del primer inventario', default=_get_fecha_inicio)
    fecha_final = fields.Date('Fecha del úlitmo inventario', default=_get_fecha_fin)
    fecha_balance = fields.Date('Fecha')
    opciones_fecha = fields.Selection([('0', 'Balance anual'), ('1', 'A determinada fecha')],
                                      string="Opciones de balance", default='1')

    @api.onchange("category_id")
    def filtro_category_id(self):
        if self.category_id:
            self.ensure_one()
            prod_tmpl_ids = self.env['product.template'].search([('categ_id', '=', self.category_id.id)])
            if prod_tmpl_ids:
                prod_ids = self.env['product.product'].search([('product_tmpl_id', 'in', prod_tmpl_ids.ids)])

                return {
                    "domain": {
                        "product_id": [("id", "in", prod_ids.ids)],
                    }
                }

    def modif_fecha(self, fecha):
        modif = time.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        anio = time.strftime('%Y', modif)
        mes = time.strftime('%m', modif)
        dia = time.strftime('%d', modif)
        completo = datetime.date(int(anio), int(mes), int(dia))
        format_fecha = completo.strftime("%d-%m-%Y")
        return format_fecha

    @api.multi
    def action_export(self):
            self.ensure_one()

            if self.fecha_inicial:
                f_inicial = date(*map(int, self.fecha_inicial.split("-")))
                f_inicial = f_inicial.strftime("%Y-%m-%d")
            if self.fecha_final:
                f_final = date(*map(int, self.fecha_final.split("-")))
                f_final = f_final.strftime("%Y-%m-%d")

            # filtra el estado en las validadas...... en las facturas pagadas que este pagada

            title_lime = easyxf('pattern: pattern solid, fore_colour lime;font: bold 1;')
            title_plan = easyxf('pattern: pattern solid, fore_colour light_green;font: bold 1;')
            title_real = easyxf('pattern: pattern solid, fore_colour gold;font: bold 1;')
            title_calculos = easyxf('pattern: pattern solid, fore_colour periwinkle;font: bold 1;')
            lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
            lineas_estilo_gris = easyxf(
                'pattern:  pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
            lineas_hs = easyxf('font: name Calibri; alignment: horizontal left;font: bold 1;')

            wb = Workbook(encoding='utf8')
            ws = wb.add_sheet('Hoja 1', cell_overwrite_ok=True)
            ws1 = wb.add_sheet('Hoja 2', cell_overwrite_ok=True)
            ws2 = wb.add_sheet('Hoja 3', cell_overwrite_ok=True)

            fila = 0

            sql = ''' 
                     SELECT replace(replace(sl.complete_name,'Physical Locations / ',''),'Ubicaciones físicas / ','')::character varying as Ubicacion,
                        p.default_code::character varying as codigo,
                        p.name_template::character varying as articulo,
                        t.despues,
                        t.total,
                        pc.name::character varying as categoria,
                        ti.name::character varying as Tipo
                        
                    from sp_stock_history_fifo_ubicacion(%(fecha_balance)s,%(fecha_inicio)s, %(fecha_fin)s,%(param_ubic)s , %(param_prod)s , %(param_empaque)s,%(param_categ)s,%(param_invent)s,%(opciones_fecha)s) t
                    INNER JOIN product_product p ON p.id = t.id_producto
                    INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                    INNER JOIN stock_location sl ON sl.id = t.id_ubicacion
                    LEFT JOIN familia  fa ON  fa.id = pt.familia_id
                    LEFT JOIN tipo     ti ON  ti.id = pt,tipo_id
                    LEFT JOIN product_category pc on pc.id = pt.categ_id;
    
                '''

            # titulos
            ws.write(0, 0, "Ubicación", title_lime)
            ws.write(0, 1, 'Código', title_lime)
            ws.write(0, 2, 'Producto', title_lime)
            ws.write(0, 3, "Stock", title_lime)
            ws.write(0, 4, 'Categoría', title_lime)
            ws.write(0, 5, 'Tipo', title_lime)
            # ws.write(0, 6, 'Tipo de Bien', title_lime)
            # ws.write(0, 7, 'Inventariado', title_lime)

            self.archivo_nombre = "Reporte_Stock_ubicacion.xlsx"

            param_ubic = self.ubicacion.id if self.ubicacion else 0
            param_categoria = self.category_id.id if self.category_id else 0
            param_prod = self.product_id.id if self.product_id else 0
            # param_prod_invent = 1 if self.productos_inventariados else 0
            param_op_prod = int(0)
            param_empaque = 1



            param = {
                'fecha_inicio': self.fecha_inicial,
                'fecha_fin': self.fecha_final,
                'param_ubic': param_ubic,
                'param_prod': param_prod,
                'param_empaque': param_empaque,
                'param_categ': param_categoria,
                'param_invent': param_op_prod,
                'fecha_balance': self.fecha_balance,
                'opciones_fecha': int(self.opciones_fecha)
            }
            # print param

            self.env.cr.execute(sql, param)
            resultado = self.env.cr.fetchall()
            contador = 0

            if len(resultado) > 0:
                estilo = lineas_estilo
                aux = None
                for res in resultado:
                    fila += 1
                    contador += 1

                    # if contador == 65000:
                    #     ws = ws1
                    #     fila = 1
                    # if contador == 130000:
                    #     ws = ws2
                    #     fila = 1




                    ws.write(fila, 0, res[0], estilo)
                    ws.write(fila, 1, res[1], estilo)
                    ws.write(fila, 2, res[2], estilo)
                    ws.write(fila, 3, res[3], estilo)
                    ws.write(fila, 4, res[4], estilo)
                    ws.write(fila, 5, res[5], estilo)
                    # ws.write(fila, 6, res[6], estilo)
                    # ws.write(fila, 7, res[7], estilo)

                    # fila += 1
                    # ws.write(fila, 0, '', lineas_estilo)



            anchos = {
                0: 20,
                1: 10,
                2: 30,
                3: 15,
                4: 15,
                5: 25,
                # 6: 25,
                # 7: 10,
                # 8: 15,
                # 9: 15,
            }

            for col in range(0, len(anchos) + 3):
                ws.col(col).width = anchos.get(col, 7) * 367

            # for col in range(0, len(titulos) + 3):
            #     ws.col(col).width = anchos.get(col, 7) * 367

            # Armo el retorno
            fp = StringIO()
            wb.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()

            data_to_save = base64.encodestring(data)

            # Nombre para el archivo
            self.write({
                'archivo_nombre': self.archivo_nombre,
                'binario': data_to_save
            })

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=dtm.amsj.stock.tipo&field=binario&id=%s&filename=%s' % (
                    self.id,
                    self.archivo_nombre,
                ),
                'target': 'self',
            }
