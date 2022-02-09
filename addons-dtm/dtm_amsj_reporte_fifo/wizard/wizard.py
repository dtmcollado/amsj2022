# -*- coding: utf-8 -*-
from openerp import models, fields, api

import base64
import xlwt
from cStringIO import StringIO
from datetime import date
from xlsxwriter.workbook import Workbook
from xlwt import Workbook, XFStyle, easyxf, Formula, Font
from lxml import etree
from openerp.exceptions import ValidationError, Warning


class wizard_reporte_fifo(models.TransientModel):
    _name = "wizard_reporte_fifo"

    CODIGO_DOSIS_UNITARIA = 'SJMDU'

    todos = fields.Boolean(string='Todos los productos?', default=True)
    product_id = fields.Many2one('product.product', string='Producto')
    date = fields.Datetime(string='Fecha del inventario',
                       index=True, copy=False, default=date.today(), required=True)
    category_id = fields.Many2one(comodel_name='product.category',string=u'Categoría interna')
    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")

    @api.onchange('category_id')
    def onchange_category_id(self):
        domain = {}
        if self.category_id:
            product_ids= self.env['product.product'].with_context(active_test=False).search([('type', '=', 'product'),('product_tmpl_id.categ_id','=',self.category_id.id)])

        else:
            product_ids= self.env['product.product'].with_context(active_test=False).search([('type', '=', 'product')])

        domain = {'product_id': '''[('id', 'in', %s)]''' % str(product_ids.ids)}
        return {'domain': domain}



    @api.multi
    def action_reporte_fifo(self):
        self.ensure_one()

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

        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        header_left = easyxf('font: name Calibri, bold True; alignment: horizontal left;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        texto = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')

        lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
        lineas_estilo_gris = easyxf('pattern:  pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
        title_lime = easyxf('pattern: pattern solid, fore_colour lime;font: bold 1;')

        fila = 0
        col = 0
        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        date = self.date.split('-')
        #ws.write_merge(fila, fila, 3, 7, U"Valoración inventario FIFO al " + date[2] + '/' + date[1] + '/' + date[0],
                      # title_big)

        if not self.todos:
            stock_location_ids = self.env['stock.location'].search([('usage','=','internal'),('codigo_amsj','!=',self.CODIGO_DOSIS_UNITARIA),('inv_contabilidad','=',True)],order='name asc')
            ws.write(fila, 0, u"Código del producto", header_left)
            ws.write(fila, 1, u"Nombre", header_left)
            ws.write(fila, 2, u"Ubicación", header_left)
            ws.write(fila, 3, u"Categoría", header_left)
            ws.write(fila, 4, u"Cantidad en ese almacen", header_left)
            fila += 1
            cantidad_total_stock = float()
            for location_id in stock_location_ids:
                cantidad_stock = float()
                stock_location_obj = self.pool.get('stock.location')
                nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id.id)[0][1]
                self.env.cr.execute(
                    'select max(h.fin) from horas_inventarios_tmp h inner join stock_inventory si on h.ubicacion_id = si.location_id where si.inv_por_contabilidad = true and h.ubicacion_id=%s',
                    (location_id.id,))
                resultados = self.env.cr.fetchall()
                for resultado in resultados:
                    date_inventory = resultado[0]
                self.env.cr.execute('select cantidad from sp_stock_history_date(%s,%s) where id_producto = %s and cantidad > 0',(date_inventory, location_id.id,self.product_id.id,))
                resultados = self.env.cr.fetchall()
                for resultado in resultados:
                    cantidad_stock += resultado[0]
                    cantidad_total_stock += cantidad_stock
                    product_category_obj = self.pool.get('product.category')
                    ws.write(fila, 0, self.product_id.default_code)
                    ws.write(fila, 1, self.product_id.name)
                    ws.write(fila, 2, nombre_almacen)
                    ws.write(fila, 3, product_category_obj.name_get(self._cr, self._uid,self.product_id.product_tmpl_id.categ_id.id)[0][1])
                    ws.write(fila, 4,cantidad_stock)
                    fila += 1
            # **************
            # Escribo el titulo
            ws.write(fila, 0, u"Fecha", header_left)
            ws.write(fila, 1, u"Factura", header_left)
            ws.write(fila, 2, u"Proveedor", header_left)
            ws.write(fila, 3, u"Cantidad comprada", header_left)
            ws.write(fila, 4, u"Precio unitario", header_left)
            ws.write(fila, 5, u"CJPU", header_left)
            ws.write(fila, 6, u"Precio total", header_left)
            fila += 1
            self.env.cr.execute('SELECT AIL.QUANTITY,AIL.PRICE_UNIT,AI.DATE_INVOICE,AI.SUPPLIER_INVOICE_NUMBER,PARTNER.NAME FROM ACCOUNT_INVOICE AI,ACCOUNT_INVOICE_LINE AIL, PRODUCT_PRODUCT P,RES_PARTNER PARTNER WHERE AI.DATE_INVOICE <= %s AND AI.TYPE = %s AND AI.STATE NOT IN %s AND AIL.INVOICE_ID = AI.ID AND P.ID = AIL.PRODUCT_ID AND AI.PARTNER_ID = PARTNER.ID ORDER BY AI.DATE_INVOICE DESC',(self.date,'in_invoice',('draft','cancel'),))
            cantidad_acumulado = float()
            resultados = self.env.cr.fetchall()
            for resultado in resultados:
                    price = float()
                    cantidad = float()
                    diferencia = float()
                    cantidad_linea = resultado[0]
                    if cantidad_acumulado < cantidad_total_stock:
                        if cantidad_acumulado == 0:
                            diferencia = cantidad_total_stock - cantidad_linea
                        else:
                            diferencia = cantidad_total_stock - cantidad_acumulado

                        if diferencia <= 0:
                            cantidad = cantidad_total_stock
                        else:
                            cantidad = diferencia
                            if cantidad_acumulado == 0:
                                cantidad = cantidad_linea

                        cantidad_acumulado = cantidad_acumulado + cantidad
                        price = abs(round(price + (resultado[1] * cantidad), 2))
                        date_invoice =resultado[2].split('-')

                        ws.write(fila, 0, date_invoice[2] + '/' + date_invoice[1] + '/' + date_invoice[0])
                        ws.write(fila, 1, resultado[3])
                        ws.write(fila, 2, resultado[4])
                        ws.write(fila, 3, cantidad)
                        ws.write(fila, 4, abs(round(resultado[1],2)))
                        ws.write(fila, 5, 0)
                        ws.write(fila, 6, abs(price))
                        fila += 1

            if cantidad_acumulado == 0:
                precio_unitario = round(self.product_id.product_tmpl_id.standard_price,2)
                price = round((self.product_id.product_tmpl_id.standard_price * cantidad_total_stock), 2)
                ws.write(fila, 0, '24/07/2020')
                ws.write(fila, 1, u'N/A')
                ws.write(fila, 2, 'CARGA INICIAL')
                ws.write(fila, 3, cantidad_total_stock)
                ws.write(fila, 4, abs(precio_unitario))
                ws.write(fila, 5, 0)
                ws.write(fila, 6, abs(price))
                fila += 1
        else:
            product_ids = self.env['product.product'].with_context(active_test=False).search([('type', '=', 'product')],order = 'name asc')
            if self.category_id:
                product_ids = self.env['product.product'].with_context(active_test=False).search(
                        [('type', '=', 'product'),('product_tmpl_id.categ_id','=',self.category_id.id)],order = 'name asc')
            
            cantidad_total_stock = float()
            product_ids = product_ids.ids
            
            ws.write(fila, 0, u"Código del producto", title_lime)
            ws.write(fila, 1, u"Nombre", title_lime)
            ws.write(fila, 2, u"Ubicación", title_lime)
            ws.write(fila, 3, u"Categoría", title_lime)
            ws.write(fila, 4, u"Cantidad en ese almacen", title_lime)
            ws.write(fila, 5, "", title_lime)
            ws.write(fila, 6, "", title_lime)
            fila += 1
            # **************
            # Escribo el titulo
            ws.write(fila, 0, u"Fecha", header_left)
            ws.write(fila, 1, u"Factura", header_left)
            ws.write(fila, 2, u"Proveedor", header_left)
            ws.write(fila, 3, u"Cantidad comprada", header_left)
            ws.write(fila, 4, u"Precio unitario", header_left)
            ws.write(fila, 5, u"CJPU", header_left)
            ws.write(fila, 6, u"Precio total", header_left)
            fila += 1

            for product in product_ids:
                stock_location_obj = self.pool.get('stock.location')
                
                # stock_location_ids = self.env['stock.location'].search(
                #     [('usage', '=', 'internal'), ('codigo_amsj', '!=', self.CODIGO_DOSIS_UNITARIA),
                #      ('inv_contabilidad', '=', True)], order='name asc')
                # import ipdb; ipdb.set_trace()

                #self.env.cr.execute('''SELECT distinct(sq.location_id) 
                #    FROM stock_quant sq inner join stock_location sl on sl.id = sq.location_id 
                #    WHERE sq.qty > 0 and sl.inv_contabilidad = True and sl.usage ::text  in ('internal') 
                #    and sl.codigo_amsj != 'SJMDU' and sq.product_id = %s''',(product,))
                #stock_location_ids = self.env.cr.fetchall()

                self.env.cr.execute('''select id as location_id from stock_location where inv_contabilidad = true''')
                stock_location_ids = self.env.cr.fetchall()
                
                if len(stock_location_ids) > 0:
                    for location_id in stock_location_ids:

                        nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id)[0][1]
                       
                        # stock_quant_ids = self.env.cr.execute('SELECT AIL.QUANTITY,AIL.PRICE_UNIT,AI.DATE_INVOICE FROM ACCOUNT_INVOICE AI,ACCOUNT_INVOICE_LINE AIL, PRODUCT_PRODUCT P WHERE AI.DATE_INVOICE <= %s AND AI.TYPE = %s AND AI.STATE NOT IN %s AND AIL.INVOICE_ID = AI.ID AND P.ID = AIL.PRODUCT_ID ORDER BY AI.DATE_INVOICE DESC',(self.date,'in_invoice',('draft','cancel'),))
                        self.env.cr.execute(
                                'select max(h.fin) from horas_inventarios_tmp h inner join stock_inventory si on h.ubicacion_id = si.location_id where si.inv_por_contabilidad = true and h.ubicacion_id=%s',
                            (location_id,))
                        cantidad_stock = float()
                        resultados = self.env.cr.fetchall()
                        for resultado in resultados:
                            date_inventory = resultado[0]


                        #self.env.cr.execute(
                        #    'select cantidad from sp_stock_history_date(%s,%s) where id_producto = %s and cantidad > 0',
                        #    (date_inventory, location_id, product))

                        self.env.cr.execute('''select cantidad 
                            from (
                                select sum(coalesce(cantidad_despues,0)) as cantidad 
                                from temp_stock_history_date_product where producto_id=%s and ubicacion_id=%s
                            ) as t where t.cantidad > 0''', (product, location_id))
                        resultados = self.env.cr.fetchall()

                        # self.env.cr.execute(
                        #     'select cantidad from sp_stock_history_date(%s,%s) where id_producto = %s and cantidad > 0',
                        #     (date_inventory, location_id.id, product.id,))
                        # resultados = self.env.cr.fetchall()
                        for resultado in resultados:
                            cantidad_stock += resultado[0]
                        if cantidad_stock > 0:
                            cantidad_total_stock += cantidad_stock
                        # ws.write(fila, 0, u"Código del producto", header_left)
                        # ws.write(fila, 1, u"Nombre", header_left)
                        # ws.write(fila, 2, u"Ubicación", header_left)
                        # ws.write(fila, 3, u"Categoría", header_left)
                        # ws.write(fila, 4, u"Cantidad en ese almacen", header_left)
                        # fila += 1
                            estilo=None
                            if fila%2==0:
                                estilo=lineas_estilo_gris
                            else:
                                estilo=lineas_estilo

                            product_obj = self.env['product.product'].with_context(active_test=False).search([('id','=',product)])
                            product_category_obj = self.pool.get('product.category')
                            ws.write(fila, 0, product_obj.default_code, estilo)
                            ws.write(fila, 1, product_obj.name, estilo)
                            ws.write(fila, 2, nombre_almacen, estilo)

                            # ws.write(fila, 3, product_obj_category_obj.name_get(self._cr, self._uid,product_obj.product_obj_tmpl_id.categ_id.id)[0][1])
                            ws.write(fila, 3, product_obj.product_tmpl_id.categ_id.name,estilo)

                            ws.write(fila, 4, cantidad_stock, estilo)
                            ws.write(fila, 5, '', estilo)
                            ws.write(fila, 6, '', estilo)
                            fila += 1
    
                            self.env.cr.execute('''SELECT AIL.QUANTITY,AIL.PRICE_UNIT,AI.DATE_INVOICE,AI.supplier_invoice_number,PARTNER.NAME, t.cjpu 
                                                    FROM ACCOUNT_INVOICE AI 
                                                    INNER JOIN ACCOUNT_INVOICE_LINE AIL ON AIL.INVOICE_ID = AI.ID 
                                                    INNER JOIN PRODUCT_PRODUCT P ON P.ID = AIL.PRODUCT_ID
                                                    INNER JOIN RES_PARTNER PARTNER ON AI.PARTNER_ID = PARTNER.ID 
                                                    left join (
                                                        select invoice_line_id as cjpu
                                                        from account_invoice_line_tax 
                                                        where tax_id=17
                                                    ) t on t.cjpu = ail.id

                                                    WHERE AI.DATE_INVOICE <= %s AND AI.TYPE = %s 
                                                    AND AI.STATE NOT IN %s AND P.ID = %s 
                                                    ORDER BY AI.DATE_INVOICE DESC''',(self.date, 'in_invoice', ('draft', 'cancel'),product_obj.id))
                            resultados = self.env.cr.fetchall()
                            
                            cantidad_acumulado = float()
                            for resultado in resultados:
                                price = float()
                                cantidad = float()
                                diferencia = float()
                                cantidad_linea = resultado[0]

                                if fila%2==0:
                                    estilo=lineas_estilo_gris
                                else:
                                    estilo=lineas_estilo

                                if cantidad_acumulado < cantidad_stock:
                                    if cantidad_acumulado == 0:
                                        diferencia = cantidad_stock - cantidad_linea
                                    else:
                                        diferencia = cantidad_stock - cantidad_acumulado

                                    if diferencia <= 0:
                                        cantidad = cantidad_stock
                                    else:
                                        cantidad = diferencia
                                        if cantidad_acumulado == 0:
                                            cantidad = cantidad_linea

                                    cjpu = 0
                                    cantidad_acumulado = cantidad_acumulado + cantidad
                                    if resultado[5]:
                                        cjpu = float(resultado[1]) *0.02
                                    price = abs(round(price + ((resultado[1]+cjpu) * cantidad), 2))
                                    
                                    date_invoice = resultado[2].split('-')
                                    ws.write(fila, 0,date_invoice[2] + '/' + date_invoice[1] + '/' + date_invoice[0],estilo)
                                    ws.write(fila, 1, resultado[3],estilo)
                                    ws.write(fila, 2, resultado[4],estilo)
                                    ws.write(fila, 3, cantidad,estilo)
                                    ws.write(fila, 4, abs(round(resultado[1],2)),estilo)
                                    ws.write(fila, 5, cjpu,estilo)
                                    ws.write(fila, 6, price,estilo)
                                    fila += 1
                            if cantidad_acumulado == 0:
                                if fila%2==0:
                                    estilo=lineas_estilo_gris
                                else:
                                    estilo=lineas_estilo
                                #price = round((product_obj.product_tmpl_id.standard_price * cantidad_total_stock), 2)
                                precio_unitario = product_obj.product_tmpl_id.standard_price
                                price = round((precio_unitario * cantidad_stock), 2)
                                
                                ws.write(fila, 0, '24/07/2020',estilo)
                                ws.write(fila, 1, u'N/A',estilo)
                                ws.write(fila, 2, 'CARGA INICIAL',estilo)
                                ws.write(fila, 3, cantidad_stock,estilo)
                                ws.write(fila, 4, abs(precio_unitario),estilo)
                                ws.write(fila, 5, 0,estilo)
                                ws.write(fila, 6, abs(price),estilo)
                                fila += 1
            fila += 1
            ws.write(fila, 4, u"CANTIDAD TOTAL: " + str(cantidad_total_stock), header_left)
        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)
        fecha = date[2] + '-' + date[1] + '-' + date[0]
        nombre_archivo = 'Valoracion_Fifo_al_' + fecha

        # Nombre para el archivo
        self.write({
            'archivo_nombre': nombre_archivo + ".xls",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard_reporte_fifo&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }

    @api.multi
    def action_reporte_fifo_resumen_nuevo(self):
        self.ensure_one()

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

        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        header_left = easyxf('font: name Calibri, bold True; alignment: horizontal left;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        texto = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')

        fila = 0
        col = 0
        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        date = self.date.split('-')
        #ws.write_merge(fila, fila, 3, 7, U"Resumen FIFO al " + date[2] + '/' + date[1] + '/' + date[0],
                      # title_big)

        if not self.todos:
            stock_location_ids = self.env['stock.location'].search([('usage','=','internal'),('codigo_amsj','!=',self.CODIGO_DOSIS_UNITARIA),('inv_contabilidad','=',True)],order='name asc')
            for location_id in stock_location_ids:
                stock_location_obj = self.pool.get('stock.location')
                nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id.id)[0][1]
                self.env.cr.execute(
                    'select max(h.fin) from horas_inventarios_tmp h inner join stock_inventory si on h.ubicacion_id = si.location_id where si.inv_por_contabilidad = true and h.ubicacion_id=%s',
                    (location_id.id,))
                cantidad_stock = float()
                resultados = self.env.cr.fetchall()
                for resultado in resultados:
                    date_inventory = resultado[0]
                self.env.cr.execute(
                    'select cantidad from sp_stock_history_date(%s,%s) where id_producto = %s and cantidad > 0',
                    (date_inventory, location_id.id, self.product_id.id,))
                resultados = self.env.cr.fetchall()
                for resultado in resultados:
                    cantidad_stock += resultado[0]
                if cantidad_stock > 0:
                    # **************
                    # Escribo el titulo
                    ws.write(fila, 0, u"Código de producto", header_left)
                    ws.write(fila, 1, u"Nombre", header_left)
                    ws.write(fila, 2, u"Categoría", header_left)
                    ws.write(fila, 3, u"Ubicación", header_left)
                    ws.write(fila, 4, u"Cantidad", header_left)
                    ws.write(fila, 5, u"FIFO Unitario", header_left)
                    ws.write(fila, 6, u"FIFO Total", header_left)
                    fila += 1
                    self.env.cr.execute('SELECT AIL.QUANTITY,AIL.PRICE_UNIT,AI.DATE_INVOICE FROM ACCOUNT_INVOICE AI,ACCOUNT_INVOICE_LINE AIL, PRODUCT_PRODUCT P WHERE AI.DATE_INVOICE <= %s AND AI.TYPE = %s AND AI.STATE NOT IN %s AND AIL.INVOICE_ID = AI.ID AND P.ID = AIL.PRODUCT_ID ORDER BY AI.DATE_INVOICE DESC',(self.date,'in_invoice',('draft','cancel'),))
                    cantidad_acumulado = float()
                    resultados = self.env.cr.fetchall()
                    price = float()
                    cantidad = float()
                    diferencia = float()
                    for resultado in resultados:
                        cantidad_linea = resultado[0]
                        if cantidad_acumulado < cantidad_stock:
                            if cantidad_acumulado == 0:
                                diferencia = cantidad_stock - cantidad_linea
                            else:
                                diferencia = cantidad_stock - cantidad_acumulado

                            if diferencia <= 0:
                                cantidad = cantidad_stock
                            else:
                                 cantidad = diferencia
                                 if cantidad_acumulado == 0:
                                    cantidad = cantidad_linea

                            cantidad_acumulado = cantidad_acumulado + cantidad
                            price += abs(round((resultado[1] * cantidad), 2))

                    if cantidad_acumulado > 0:
                        product_category_obj = self.pool.get('product.category')
                        ws.write(fila, 0, self.product_id.default_code or u'Sin código')
                        ws.write(fila, 1, self.product_id.name)
                        ws.write(fila, 2, product_category_obj.name_get(self._cr, self._uid,self.product_id.product_tmpl_id.categ_id.id)[0][1])
                        ws.write(fila, 3, nombre_almacen)
                        ws.write(fila, 4, cantidad_acumulado)
                        ws.write(fila, 5, abs(round(price/cantidad_acumulado,2)))
                        ws.write(fila, 6, abs(price))
                        fila += 1
                    if cantidad_acumulado == 0:
                        price = round((self.product_id.product_tmpl_id.standard_price * cantidad_stock), 2)
                        product_category_obj = self.pool.get('product.category')
                        ws.write(fila, 0, self.product_id.default_code or u'Sin código')
                        ws.write(fila, 1, self.product_id.name)
                        ws.write(fila, 2, product_category_obj.name_get(self._cr, self._uid,
                                                                        self.product_id.product_tmpl_id.categ_id.id)[0][
                            1])
                        ws.write(fila, 3, nombre_almacen)
                        ws.write(fila, 4, cantidad_stock)
                        ws.write(fila, 5, abs(round(self.product_id.product_tmpl_id.standard_price),2))
                        ws.write(fila, 6, abs(price))
                        fila += 1

        else:
            product_ids = self.env['product.product'].with_context(active_test=False).search([('type', '=', 'product')],order = 'name desc')
            if self.category_id:
                product_ids = self.env['product.product'].with_context(active_test=False).search(
                    [('type', '=', 'product'),('product_tmpl_id.categ_id','=',self.category_id.id)],order = 'name desc')

            #stock_location_ids = self.env['stock.location'].search([('usage','=','internal'),('codigo_amsj','!=',self.CODIGO_DOSIS_UNITARIA),('inv_contabilidad','=',True)],order='name asc')
            # **************
            # Escribo el titulo
            ws.write(fila, 0, u"Código de producto", header_left)
            ws.write(fila, 1, u"Nombre", header_left)
            ws.write(fila, 2, u"Categoría", header_left)
            ws.write(fila, 3, u"Ubicación", header_left)
            ws.write(fila, 4, u"Cantidad", header_left)
            ws.write(fila, 5, u"FIFO Unitario", header_left)
            ws.write(fila, 6, u"FIFO Total", header_left)
            fila += 1
            if product_ids:
                product_ids = product_ids.ids
            
            for product in product_ids:

                self.env.cr.execute('''SELECT distinct(sq.location_id) 
                    FROM stock_quant sq inner join stock_location sl on sl.id = sq.location_id 
                    WHERE sq.qty > 0 and sl.inv_contabilidad = True and sl.usage ::text  in ('internal') 
                    and sl.codigo_amsj != 'SJMDU' and sq.product_id = %s''',(product,))
                
                stock_location_ids = self.env.cr.fetchall()

                stock_location_obj = self.pool.get('stock.location')
                if len(stock_location_ids) > 0:
                    for location_id in stock_location_ids:
                        nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id)[0][1]
                        self.env.cr.execute(
                            'select max(h.fin) from horas_inventarios_tmp h inner join stock_inventory si on h.ubicacion_id = si.location_id where si.inv_por_contabilidad = true and h.ubicacion_id=%s',
                            (location_id,))
                        cantidad_stock = float()
                        resultados = self.env.cr.fetchall()
                        for resultado in resultados:
                            date_inventory = resultado[0]
                        self.env.cr.execute(
                            'select cantidad from sp_stock_history_date(%s,%s) where id_producto = %s and cantidad > 0',
                            (date_inventory, location_id, product,))
                        resultados = self.env.cr.fetchall()
                        for resultado in resultados:
                            cantidad_stock += resultado[0]
                        if cantidad_stock > 0:
                            self.env.cr.execute(
                                'SELECT AIL.QUANTITY,AIL.PRICE_UNIT,AI.DATE_INVOICE,AI.supplier_invoice_number,PARTNER.NAME FROM ACCOUNT_INVOICE AI,ACCOUNT_INVOICE_LINE AIL, PRODUCT_PRODUCT P,RES_PARTNER PARTNER WHERE AI.DATE_INVOICE <= %s AND AI.TYPE = %s AND AI.STATE NOT IN %s AND AIL.INVOICE_ID = AI.ID AND P.ID = AIL.PRODUCT_ID AND AI.PARTNER_ID = PARTNER.ID AND P.ID = %s ORDER BY AI.DATE_INVOICE DESC',
                                (self.date, 'in_invoice', ('draft', 'cancel'),product,))
                            resultados = self.env.cr.fetchall()
                            cantidad_acumulado = float()
                            price = float()
                            cantidad = float()
                            diferencia = float()
                            for resultado in resultados:
                                cantidad_linea=resultado[0]
                                if cantidad_acumulado < cantidad_stock:
                                    if cantidad_acumulado == 0:
                                        diferencia = cantidad_stock - cantidad_linea
                                    else:
                                        diferencia = cantidad_stock - cantidad_acumulado

                                    if diferencia <= 0:
                                        cantidad = cantidad_stock
                                    else:
                                        cantidad = diferencia
                                        if cantidad_acumulado == 0:
                                            cantidad = cantidad_linea
                                    cantidad_acumulado = cantidad_acumulado + cantidad
                                    price += abs(round((resultado[1] * cantidad), 2))
                                else:
                                    break
                            if cantidad_acumulado> 0:
                                product_obj = self.env['product.product'].with_context(active_test=False).search([('id','=',product)])
                                product_category_obj = self.pool.get('product.category')
                                ws.write(fila, 0, product_obj.default_code or u'Sin código')
                                ws.write(fila, 1, product_obj.name)
                                ws.write(fila, 2, product_category_obj.name_get(self._cr, self._uid,
                                                                                product_obj.product_tmpl_id.categ_id.id)[0][
                                    1])
                                ws.write(fila, 3, nombre_almacen)
                                ws.write(fila, 4, cantidad_acumulado)
                                ws.write(fila, 5, abs(round(price/cantidad_acumulado,2)))
                                ws.write(fila, 6, abs(price))
                                fila += 1
                            if cantidad_acumulado == 0:
                                price = round((product_obj.product_tmpl_id.standard_price * cantidad_stock), 2)
                                product_category_obj = self.pool.get('product.category')
                                ws.write(fila, 0, product_obj.default_code or u'Sin código')
                                ws.write(fila, 1, product_obj.name)
                                ws.write(fila, 2, product_category_obj.name_get(self._cr, self._uid,
                                                                                product_obj.product_tmpl_id.categ_id.id)[
                                    0][
                                    1])
                                ws.write(fila, 3, nombre_almacen)
                                ws.write(fila, 4, cantidad_stock)
                                ws.write(fila, 5, abs(product_obj.product_tmpl_id.standard_price))
                                ws.write(fila, 6, abs(price))
                                fila += 1

        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)
        fecha = date[2] + '-' + date[1] + '-' + date[0]
        nombre_archivo = 'Resumen_Fifo_al_' + fecha

        # Nombre para el archivo
        self.write({
            'archivo_nombre': nombre_archivo + ".xls",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard_reporte_fifo&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }

    @api.multi
    def action_reporte_sin_detalle(self):
        self.ensure_one()

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

        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        header_left = easyxf('font: name Calibri, bold True; alignment: horizontal left;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        texto = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')

        fila = 0
        col = 0
        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        date = self.date.split('-')
        ws.write_merge(fila, fila, 3, 7, U"Stock por ubicación al " + date[2] + '/' + date[1] + '/' + date[0],
                       title_big)

        if not self.todos:
            for location_id in self.stock_location_ids:
                stock_location_obj = self.pool.get('stock.location')
                nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id.id)[0][1]
                stock_quant_ids = self.env['stock.quant'].search(
                    [('location_id', '=', location_id.id), ('product_id', '=', self.product_id.id),
                     ('in_date', '<=', self.date)])
                cantidad_stock = float()
                for stock_quant in stock_quant_ids:
                    cantidad_stock = stock_quant.qty + cantidad_stock
                if cantidad_stock > 0:
                    if location_id.codigo_amsj == 'SJMDU':
                        lista_material_id = self.env['mrp.bom'].search(
                            [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)], limit=1)
                        if len(lista_material_id) > 0:
                            if lista_material_id.product_qty == 0:
                                cantidad_stock = 0
                            else:
                                cantidad_stock = round((cantidad_stock / lista_material_id.product_qty), 2)
                    ws.write(fila, 1, u"ALMACEN: " + nombre_almacen, header_left)
                    fila += 1
                    ws.write(fila, 1, u"PRODUCTO", header_left)
                    ws.write(fila, 2, u"CANTIDAD", header_left)
                    fila += 1
                    ws.write(fila, 1, self.product_id.name, header_left)
                    ws.write(fila, 2, str(cantidad_stock), header_left)
                    fila += 3
        else:
            product_ids = self.env['product.product'].with_context(active_test=False).search([('type', '=', 'product')],order = 'name desc')
            for location_id in self.stock_location_ids:
                stock_location_obj = self.pool.get('stock.location')
                nombre_almacen = stock_location_obj.name_get(self._cr, self._uid, location_id.id)[0][1]
                fila += 1
                ws.write(fila, 1, u"ALMACEN: " + nombre_almacen, header_left)
                fila += 3
                ws.write(fila, 1, u"PRODUCTO", header_left)
                ws.write(fila, 2, u"CANTIDAD", header_left)
                fila += 1
                for product in product_ids:
                    stock_quant_ids = self.env['stock.quant'].search(
                        [('location_id', '=', location_id.id), ('product_id', '=', product.id),
                         ('in_date', '<=', self.date)])
                    cantidad_stock = float()
                    for stock_quant in stock_quant_ids:
                        cantidad_stock = stock_quant.qty + cantidad_stock
                    if cantidad_stock > 0:
                        if location_id.codigo_amsj == 'SJMDU':
                            lista_material_id = self.env['mrp.bom'].search(
                                [('product_tmpl_id', '=', product.product_tmpl_id.id)], limit=1)
                            if len(lista_material_id) > 0:
                                if lista_material_id.product_qty == 0:
                                    cantidad_stock = 0
                                else:
                                    cantidad_stock = round((cantidad_stock / lista_material_id.product_qty), 2)
                        ws.write(fila, 1, product.name)
                        ws.write(fila, 2, str(cantidad_stock))
                        fila += 1

        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)
        fecha = date[2] + '-' + date[1] + '-' + date[0]
        nombre_archivo = 'Stock_por_ubicacion' + fecha

        # Nombre para el archivo
        self.write({
            'archivo_nombre': nombre_archivo + ".xls",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard_reporte_fifo&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }

