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
# -*- coding: utf-8 -*-
from openerp import models, fields, api
import base64
import xlwt
from cStringIO import StringIO
from datetime import date
from xlsxwriter.workbook import Workbook
from xlwt import Workbook, XFStyle, easyxf, Formula, Font
from lxml import etree
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from datetime import time, datetime


class dtm_amsj_remitos_pendientes_de_facturacion(models.TransientModel):
    _name = "dtm.amsj.remitos.pendientes.de.facturacion"
    sector_id = fields.Many2one('categoria', 'Sector', select=True)
    fecha_inicial = fields.Date('Fecha Inicio', default=date.today().replace(day=1))
    fecha_final = fields.Date('Fecha Fin', default=date.today())
    tipo_facturas = fields.Selection([('sin_fact', 'Sin Facturas'), ('con_fact', 'Con Facturas')],
                                     string="Seleccionar tipo de Remito ", default='con_fact')
    binario = fields.Binary(string='guardo_archivo')
    archivo_nombre = fields.Char(string='')
    valores_cero = fields.Boolean(string='Incluir facturas saldadas')

    def modif_fecha(self, fecha):
        modif = time.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        anio = time.strftime('%Y', modif)
        mes = time.strftime('%m', modif)
        dia = time.strftime('%d', modif)
        completo = datetime.date(int(anio), int(mes), int(dia))
        format_fecha = completo.strftime("%d-%m-%Y")
        return format_fecha

    @api.multi
    def action_remitos_pendientes(self):
        self.ensure_one()
        f_inicial = date(*map(int, self.fecha_inicial.split("-")))
        f_final = date(*map(int, self.fecha_final.split("-")))

        f_inicial = f_inicial.strftime("%Y-%m-%d")
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

        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')

        wb = Workbook(encoding='utf8')
        ws = wb.add_sheet('Hoja 1', cell_overwrite_ok=True)

        # titulos
        ws.write(0, 0, "Orden Compra", title_lime)
        # ws.write(0, 1, "Nro Remito", title_lime)
        ws.write(0, 1, 'Codigo Producto', title_lime)
        ws.write(0, 2, 'Nombre', title_lime)
        ws.write(0, 3, 'Cantidad Pendiente', title_lime)
        ws.write(0, 4, 'Importe Unitario', title_lime)
        ws.write(0, 5, 'Importe Total', title_lime)
        ws.write(0, 6, 'Proveedor', title_lime)
        # ws.write(0, 7, 'Diferencia no Facturada', title_lime)
        # ws.write(0, 8, 'Precio', title_lime)
        # ws.write(0, 9, 'Total Pendiente', title_lime)

        sql_po = '''
                    SELECT id
                    from purchase_order 
                    where state in ('confirmed','approved','done') and sector_id = %(sector_id)s
                   and date_order >= DATE %(fecha_desde)s and date_order <= DATE %(fecha_hasta)s
                   order by partner_id,date_order
                  '''

        self.env.cr.execute(sql_po,
                            {'fecha_desde': self.fecha_inicial + ' 00:00:00',
                             'fecha_hasta': self.fecha_final + ' 23:59:59',
                             'sector_id': self.sector_id.id
                             })
        ordenes = self.env.cr.fetchall()
        fila = 1
        if ordenes:
            for orden in ordenes:
                po = self.env['purchase.order'].browse([orden[0]])
                for p in po:
                    cantidades_facturadas = dict()
                    cantidades_pendientes = None

                    for linea in p.order_line:
                        key = self.id
                        todo = {}

                        for move in linea.move_ids:
                            if move.state == 'done' and move.invoice_state in (u'2binvoiced', u'invoiced'):
                                todo.setdefault(key, [])
                                todo[key].append(move)
                                cantidades_facturadas[move.product_id] = 0

                        facturas_ya_creadas = self.env['account.invoice'].search(
                            [('id', 'in', p.invoice_ids.ids), ('state', '!=', 'cancel')])

                        for factura_id in facturas_ya_creadas:
                            for invoice_line in factura_id.invoice_line:
                                producto = invoice_line.product_id
                                if cantidades_facturadas.get(producto) >= 0:
                                    cantidades_facturadas[producto] += invoice_line.quantity

                        cantidades_pendientes = dict()


                        # linea.move_ids.ids

                        sql_mo = """
                                                            
                                select product_id , sum(product_qty), price_unit
                                    from stock_move 
                                    where id in %s and state = 'done' and invoice_state in ('2binvoiced', 'invoiced')
                                    group by product_id, price_unit
                        """

                        self.env.cr.execute(sql_mo,(tuple(linea.move_ids.ids),))

                        movi = self.env.cr.fetchall()

                        for move in movi:

                            prod = self.env['product.product'].search([('id', '=', int(move[0]))])
                            if (int(move[1]) - cantidades_facturadas[prod]) < 0:
                                cantidades_pendientes[prod] = 0
                            else:
                                try:
                                    cantidades_pendientes[prod] = (int(move[1]) - cantidades_facturadas[prod]) + \
                                                                  cantidades_pendientes[prod]
                                except KeyError:
                                    cantidades_pendientes[prod] = (int(move[1]) - cantidades_facturadas[prod])

                        for key, value in cantidades_pendientes.items():
                            if value > 0:
                                orden_compra = po.name
                                remito = '****'
                                product_id = key
                                codigo_prod = key.default_code
                                nombre_prod = key.name
                                proveedor = po.partner_id.display_name
                                cantidad = value

                                estilo = lineas_estilo

                                if po.es_cocemi:
                                    unitario = key.precio_cocemi
                                else:
                                    unitario = key.standard_price

                                total = cantidad * unitario
                                ws.write(fila, 0, orden_compra, estilo)
                                # ws.write(fila, 1, remito, estilo)
                                ws.write(fila, 1, codigo_prod, estilo)
                                ws.write(fila, 2, nombre_prod, estilo)
                                ws.write(fila, 3, cantidad, estilo)

                                ws.write(fila, 4, unitario, numero_editable_bold)
                                ws.write(fila, 5, total, numero_editable_bold)
                                ws.write(fila, 6, proveedor, estilo)
                                # ws.write(fila, 6, res[7], estilo)
                                # ws.write(fila, 7, res[8], estilo)
                                # ws.write(fila, 8, res[9], estilo)
                                # ws.write(fila, 9, Formula(formulas[0].replace("#", str(fila + 1))), estilo)
                                # ws.write(fila, 10, res[10], estilo)
                                # ws.write(fila, 11, Formula(formulas[1].replace("#", str(fila + 1))), estilo)

                                fila += 1
                                ws.write(fila, 0, '', lineas_estilo)

            anchos = {
                0: 10,
                1: 25,
                2: 25,
                3: 20,
                4: 12,
                5: 15,
                6: 22,
                7: 8,
                8: 12,
                9: 12,
                10: 12,
                11: 12,
            }

            for col in range(0, len(anchos) + 3):
                ws.col(col).width = anchos.get(col, 7) * 367

            fp = StringIO()
            wb.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()

            data_to_save = base64.encodestring(data)

            # Nombre para el archivo
            self.write({
                'archivo_nombre': "Remitos_pendientes_de_facturacion.xlsx",
                'binario': data_to_save
            })

            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/download_document?model=dtm.amsj.remitos.pendientes.de.facturacion&field=binario&id=%s&filename=%s' % (
                    self.id,
                    self.archivo_nombre,
                ),
                'target': 'self',
            }
