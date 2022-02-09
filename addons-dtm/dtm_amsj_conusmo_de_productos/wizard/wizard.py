# -*- encoding: utf-8 -*-

import base64
from io import BytesIO
from datetime import date
import xlsxwriter
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

from dateutil.relativedelta import relativedelta
import datetime
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from ..library import operaciones as report_ops
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import json


class wizard(models.TransientModel):
    _name = "wizard.consumos_pdf"

    @api.multi
    def get_domain_sector(self):
        # 18
        # 19
        # 17  farmacia
        return [('id', '<>', 10)]

    fecha_inicial = fields.Date('Begin date', default=date.today().replace(day=1))
    fecha_final = fields.Date('End date', default=date.today())

    # sector_id = fields.Many2one('categoria', 'Sector')
    sector_ids = fields.Many2many(comodel_name='categoria',
                                  string="Sectores", domain=get_domain_sector
                                  )

    # categoria = fields.Many2one('product.category', 'Categoria')
    categoria_ids = fields.Many2many(comodel_name='product.category',
                                     string="Categorias"
                                     )

    date = fields.Date(string='Fecha',
                       index=True, copy=False, default=date.today(), required=True)

    categoria_todos = fields.Boolean('Todas las Categorias', default=False)
    sector_todos = fields.Boolean('Todos los Sectores', default=False)

    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")

    todos_FTM = fields.Boolean('FTM Todos', default=True)
    solo_consumos = fields.Boolean('Solo Consumos', default=False)
    almacen_origen_ids = fields.Many2many(comodel_name='stock.warehouse', string='Almacenes')
    origen_ids = fields.Many2many(comodel_name='stock.location',
                                  string="Ubicaciónes", compute='_compute_location_origen', readonly=False)

    almacen_destino_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_user', 'user_id', 'warehouse_id',
                                           string='Almacenes')

    destino_ids = fields.Many2many('stock.location', 'stock_location_user', 'user_id', 'location_id',
                                   compute='_compute_location_destino', string="Ubicaciónes", readonly=False)

    FTM = fields.Boolean('FTM', default=False)
    centro_costo = fields.Char(string='Centro de Costo')

    @api.one
    @api.depends('almacen_origen_ids')
    def _compute_location_origen(self):
        location_ids = []

        if self.almacen_origen_ids:
            for w in self.almacen_origen_ids:
                for loc in w.view_location_id.child_ids:
                    if not loc.scrap_location:
                        if loc.principal_del_expendio:
                            location_ids.append(loc.id)
                    for loc1 in loc.child_ids:
                        if not loc1.scrap_location:
                            if loc1.principal_del_expendio:
                                location_ids.append(loc1.id)
                        for loc2 in loc1.child_ids:
                            if not loc2.scrap_location:
                                if loc2.principal_del_expendio:
                                    location_ids.append(loc2.id)
                            for loc3 in loc2.child_ids:
                                if not loc3.scrap_location:
                                    if loc3.principal_del_expendio:
                                        location_ids.append(loc3.id)
        #
        if location_ids:
            self.origen_ids = location_ids

    @api.one
    @api.depends('almacen_destino_ids')
    def _compute_location_destino(self):
        location_ids = []

        if self.almacen_destino_ids:
            for w in self.almacen_destino_ids:
                for loc in w.view_location_id.child_ids:
                    if loc.scrap_location:
                        location_ids.append(loc.id)
                    for loc1 in loc.child_ids:
                        if loc1.scrap_location:
                            location_ids.append(loc1.id)
                        for loc2 in loc1.child_ids:
                            if loc2.scrap_location:
                                location_ids.append(loc2.id)
                                for loc3 in loc2.child_ids:
                                    if not loc3.scrap_location:
                                        location_ids.append(loc3.id)

        if location_ids:
            self.destino_ids = location_ids


    @api.multi
    def action_report(self):
        self.ensure_one()

        data = {}
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read()
        data['lineas'] = report_ops._datos_reporte(self)

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'dtm_amsj_conusmo_de_productos.invoices_conformar',
            'report_title': 'Consumos',
            'datas': data,
        }

    @api.multi
    def action_excel_report(self):
        self.ensure_one()

        final = date(*map(int, self.fecha_final.split("-")))
        inicial = final - relativedelta(months=11)

        # Creo el libro Excel
        fp = BytesIO()
        wb = xlsxwriter.Workbook(fp)
        ws = wb.add_worksheet()


        # # Estilos
        title_big = wb.add_format({'bold': True,'valign': 'top', 'font_size':12,'font_color':'#175785'})
        header = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal center'})
        title = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal left'})
        title_number = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal right','num_format':'#,##0.00;-#,##0.00;'})
        title_ice_blue = wb.add_format({'align': 'horizontal center','fg_color':'#74c4fc'})
        header_left = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left','bold': True})
        fecha = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal center','num_format':'DD/MM/YYYY'})

        lineas_estilo = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left'})

        lineas_estilo_num_int = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '0'})

        lineas_estilo_num = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '#.##0,0;-#.##0,0;'})

        fila = 0

        # Datos de la empresa y fecha de emision
        #ws.row(fila).height = 2 * 200
       # ws.write_merge(fila, fila, 3, 7, "Planilla Consumos Detallada", title_big)
        ws.write(fila, fila, "Planilla Consumos Detallada",title_big)

        ws.write(1, 0, u"Filtros", header_left)
        ws.write(2, 0, u"Rango de Fechas", header_left)
        ws.write(2, 1, u'Desde ' + self.fecha_inicial, fecha)
        ws.write(2, 2, u'Hasta ' + self.fecha_final, fecha)
        ws.write(3, 0, u"Todos los Sectores", header_left)
        if self.sector_todos or not self.sector_ids:
            todos_sectores = 'SI'
        else:
            todos_sectores = 'NO'
        ws.write(3, 1, todos_sectores)
        lista_sectores = "Sectores: "
        for sector in self.sector_ids:
            lista_sectores += sector.name + ' / '
        if self.sector_ids:
            ws.write(3, 3, lista_sectores, title)

        ws.write(4, 0, u"Todos las Categorias", header_left)
        if self.categoria_todos or not self.categoria_ids:
            todos_categoria = 'SI'
        else:
            todos_categoria = 'NO'
        ws.write(4, 1, todos_categoria)
        lista_categorias = "Categorias: "
        for categoria in self.categoria_ids:
            lista_categorias += categoria.name + ' / '
        if self.categoria_ids:
            ws.write(4, 3, lista_categorias)

        # ****
        if not self.origen_ids:
            ws.write(5, 0, u"Todos los Origenes", header_left)
        else:
            ws.write(5, 0, u"Origenes:", header_left)
            origenes = ""
            for origen in self.origen_ids:
                origenes += origen.display_name + ','
            ws.write(5, 1, origenes)

        # ****
        if not self.destino_ids:
            ws.write(6, 0, u"Todos los Destinos", header_left)
        else:
            ws.write(6, 0, u"Destinos:", header_left)

            destinos = ""
            for destino in self.destino_ids:
                destinos += destino.display_name + ','
            ws.write(6, 1, destinos)

        fila += 10

        # **************

        # Escribo el titulo
        ws.write(fila, 0, u"Sector", title_ice_blue)
        ws.write(fila, 1, u"Fecha", title_ice_blue)
        ws.write(fila, 2, u"Categoria Interna", title_ice_blue)
        ws.write(fila, 3, u"Rubro del Producto", title_ice_blue)
        ws.write(fila, 4, u"Desc Rubro del Producto", title_ice_blue)

        ws.write(fila, 5, u"Rubro Consumo Producto", title_ice_blue)
        ws.write(fila, 6, u"Desc Rubro Consumo Producto", title_ice_blue)

        ws.write(fila, 7, u"Código", title_ice_blue)
        ws.write(fila, 8, u"Producto", title_ice_blue)
        ws.write(fila, 9, u"Cantidad", title_ice_blue)
        ws.write(fila, 10, u"Valor FIFO Unitario", title_ice_blue)

        ws.write(fila, 11, u"CJPU (Unitario)", title_ice_blue)

        ws.write(fila, 12, u"Importe FIFO", title_ice_blue)
        ws.write(fila, 13, u"Valor Ult. Compra Unit.", title_ice_blue)

        ws.write(fila, 14, u"CJPU (Ult. Compra Unit.)", title_ice_blue)

        ws.write(fila, 15, u"Importe Ult. Compra", title_ice_blue)

        ws.write(fila, 16, u"Principio Activo", title_ice_blue)
        ws.write(fila, 17, u"Familia", title_ice_blue)
        ws.write(fila, 18, u"Grupo", title_ice_blue)
        ws.write(fila, 19, u"SubGrupo", title_ice_blue)
        ws.write(fila, 20, u"Forma Farmaceutica", title_ice_blue)
        ws.write(fila, 21, u"Almacen Origen", title_ice_blue)
        ws.write(fila, 22, u"CC Origen", title_ice_blue)
        ws.write(fila, 23, u"Centro Costo Origen", title_ice_blue)
        ws.write(fila, 24, u"Ubicación Origen", title_ice_blue)
        ws.write(fila, 25, u"Almacen Destino", title_ice_blue)
        ws.write(fila, 26, u"CC Destino", title_ice_blue)
        ws.write(fila, 27, u"Centro Costo Destino", title_ice_blue)
        ws.write(fila, 28, u"Ubicación Destino", title_ice_blue)
        ws.write(fila, 29, u"Usuario", title_ice_blue)
        ws.write(fila, 30, u"Proveedor", title_ice_blue)
        ws.write(fila, 31, u"Tipo de bien", title_ice_blue)
        ws.write(fila, 32, u"Tipo de Ubicación", title_ice_blue)
        fila += 1

        consulta = """select
                              sector, 
                              TO_CHAR(fecha :: DATE, 'dd/mm/yyyy'),
    			              categoria_interna,	
    			 '-' as RubroCategoriaGastos,
    			 '-' as DescripRubroCategoriaGastos,
    			 '-' as aGastos,
    			 '-' as Gastos,
                              CodMSP,
                              product_template_name,
                              product_qty,
                  ValorFIFOUnitario as ValorFIFOUnitario,
                  CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN ValorFIFOUnitario * 0.02
                            ELSE 0 
                  END as CJPU,
                  
    		  CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN  total_fifo * 1.02
                   ELSE total_fifo END as costo_fifo,  		  
    			  		    
    	  		  ValorUltCompraUnit as ValorUltCompraUnit,
      		  CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN ValorUltCompraUnit * 0.02
                            ELSE 0 
                  END as CJPU_ult_compra,

                  CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN total_ultima_compra * 1.02
                  ELSE total_ultima_compra 
                  END as costo_compra,              
    			  'N/A' as p_activo,
    			  familia,		
    			  grupo,
                          subgrupo,	
    			  forma_farmaceutica,	
    			  Almacen_Origen
    			  , rubroentrada as RubroOrigen,
                          rubro_centro_entrada as CentroCostoOrigen,
    			  origen as UbicacionOrigen,
    			  Almacen_Destino, rubrosalida as RubroDestino,
    			  rubro_centro_salida as CentroCostoDestino,	
    			  destino as UbicacionDestino,usuario
    			  ,proveedor                                                  
                          ,product_template_id , es_de_consumo , destino_id

                  FROM sp_consumos_mov_report(%(ffecha_i)s,%(ffecha_f)s,%(sector_ids)s,%(es_de_consumo)s,%(categoria_ids)s,%(origen_ids)s,%(destino_ids)s) """

        
        if self.sector_ids:
            sector_ids_str = json.dumps(self.sector_ids.ids).replace('[','').replace(']','')

        if self.categoria_ids:
            categoria_ids_str = json.dumps(self.categoria_ids.ids).replace('[','').replace(']','')
        
        if self.origen_ids:
            origen_ids_str = json.dumps(self.origen_ids.ids).replace('[','').replace(']','')

        if self.destino_ids:
            destino_ids_str = json.dumps(self.destino_ids.ids).replace('[','').replace(']','')


        vals = {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                             'ffecha_f': self.fecha_final + ' 23:59:59',
                             'sector_ids': sector_ids_str if self.sector_ids else '',
                             'categoria_ids': categoria_ids_str if self.categoria_ids else '' ,
                             'origen_ids': origen_ids_str if self.origen_ids else '',
                             'destino_ids': destino_ids_str if self. destino_ids else '',
                             'es_de_consumo':1 if self.solo_consumos else 0
                             }
        
        self.env.cr.execute(consulta, vals)

        resultado = self.env.cr.fetchall()


        # Escribo una linea por producto encontrado
        # La última columna es para el color

        for producto in resultado:
            # fuente = Font()
            # fuente.name = "Calibri"
            #
            # # if producto[-1]:
            # #     fuente.colour_index = xlwt.Style.colour_map[producto[-1]]
            #
            # estilo = XFStyle()
            # estilo.font = fuente

            # Escribo los datos de cada producto
            for columna, dato in enumerate(producto):

                if columna == 12:
                    importe_fifo = float(dato)

                if columna == 15:
                    importe_puc = float(dato)

                if columna == 31:
                    producto_id = int(dato)
                    producto_obj = self.env['product.template'].search([('id', '=', producto_id)])
                    rubro_codigo_gastos_code = producto_obj.categ_id.property_account_expense_categ.code
                    rubro_codigo_gastos_name = producto_obj.categ_id.property_account_expense_categ.name

                    rubro_de_consumo_code = producto_obj.property_account_expense.code
                    rubro_de_consumo_name = producto_obj.property_account_expense.name

                    tax_ids = producto_obj.supplier_taxes_id

                    # tiene_impuesto = True
                    # for tax in tax_ids:
                    #     if int(tax) == 17:
                    #         tiene_impuesto = True

                    if int(rubro_de_consumo_code) == 0:
                        rubro_de_consumo_code = ' '
                        rubro_de_consumo_name = ' '

                    # code name
                    # product Almacenable
                    # consu   Consumible
                    # service Servicio

                    tipos = {
                        'product': 'Almacenable',
                        'consu': 'Consumible',
                        'service': 'Servicio'}

                    ws.write(fila, columna, dato, lineas_estilo_num_int)
                    ws.write(fila, 3, rubro_codigo_gastos_code, lineas_estilo)
                    ws.write(fila, 4, rubro_codigo_gastos_name, lineas_estilo)
                    ws.write(fila, 31, tipos.get(producto_obj.type, "-------"), lineas_estilo)
                    ws.write(fila, 5, rubro_de_consumo_code, lineas_estilo)
                    ws.write(fila, 6, rubro_de_consumo_name, lineas_estilo)

                    # if not tiene_impuesto:
                    #     ws.write(fila, 11, 0, lineas_estilo_gris_num)
                    #     ws.write(fila, 14, 0, lineas_estilo_gris_num)
                    # else:
                    # el_dos_porciento = importe_fifo * 0.02
                    # el_dos_puc = importe_puc * 0.02
                    # ws.write(fila, 12, importe_fifo, )
                    # ws.write(fila, 15, importe_puc, lineas_estilo_num)
                    ws.write(fila, 12, importe_fifo,lineas_estilo_num)
                    ws.write(fila, 15, importe_puc,lineas_estilo_num)

                if columna == 9:
                    ws.write(fila, columna, dato, lineas_estilo_num_int)
                else:
                    if columna == 32:
                        # if int(producto[33]) == 7:
                        #     ws.write(fila, columna, "Consumo", lineas_estilo)
                        # else:
                        if dato == 1:
                            ws.write(fila, columna, "Consumo", lineas_estilo)
                        if dato == 0:
                            ws.write(fila, columna, "Interno", lineas_estilo)

                    # -- 1 = verdadero
                    # -- 0 = falso

                    if (columna == 10) or (columna == 11) or (columna == 12) or (columna == 13) or (columna == 14) or (
                            columna == 15):
                        ws.write(fila, columna, dato, lineas_estilo)


                    else:
                        if (columna != 31) and (columna != 32) and (columna != 33):
                            ws.write(fila, columna, dato, lineas_estilo)


            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 15,
            1: 10,
            2: 35,
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
            ws.set_column(0, col, 15)
        # Armo el retorno

        wb.close()
        fp.seek(0)
        data = fp.read()
        fp.close()
        #data_to_save = base64.decodebytes(data)

        # fp = StringIO()
        # wb.close()
        # wb.save(fp)
        # fp.seek(0)
        # data = fp.read()
        # fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Consumos_Detallado.xlsx",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.consumos_pdf&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }

    @api.multi
    def action_excel_report_resumen(self):
        self.ensure_one()

        final = date(*map(int, self.fecha_final.split("-")))
        inicial = final - relativedelta(months=11)

        # Creo el libro Excel
        fp = BytesIO()
        wb = xlsxwriter.Workbook(fp)
        ws = wb.add_worksheet()


        #wb = Workbook(encoding='utf-8')
        #ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)

        # Estilos
        # # Estilos
        title_big = wb.add_format({'bold': True,'valign': 'top', 'font_size':12,'font_color':'#175785'})
        header = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal center'})
        title = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal left'})
        title_number = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal right','num_format':'#,##0.00;-#,##0.00;'})
        title_ice_blue = wb.add_format({'align': 'horizontal center','fg_color':'#74c4fc'})
        header_left = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left','bold': True})
        fecha = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal center','num_format':'DD/MM/YYYY'})

        lineas_estilo = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left'})

        lineas_estilo_num_int = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '0'})

        lineas_estilo_num = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '#.##0,0;-#.##0,0;'})

        fila = 0

        # Datos de la empresa y fecha de emision
        #ws.row(fila).height = 2 * 200
        ws.write(fila, fila, "Planilla Consumos Resumen ( solo Consumos )", title_big)

        # ws.write(1, 0, u"Filtros", header_left)
        ws.write(2, 0, u"Rango de Fechas", header_left)
        ws.write(2, 1, u'Desde ' + self.fecha_inicial, fecha)
        ws.write(2, 2, u'Hasta ' + self.fecha_final, fecha)
        ws.write(3, 0, u"Todos los Sectores", header_left)
        if self.sector_todos or not self.sector_ids:
            todos_sectores = 'SI'
        else:
            todos_sectores = 'NO'
        ws.write(3, 1, todos_sectores)
        lista_sectores = "Sectores: "
        for sector in self.sector_ids:
            lista_sectores += sector.name + ' / '
        if self.sector_ids:
            ws.write(3, 3, lista_sectores, title)
        # *
        ws.write(4, 0, u"Todos las Categorias", header_left)
        if self.categoria_todos or not self.categoria_ids:
            todos_categoria = 'SI'
        else:
            todos_categoria = 'NO'
        ws.write(4, 1, todos_categoria)
        lista_categorias = "Categorias: "
        for categoria in self.categoria_ids:
            lista_categorias += categoria.name + ' / '
        if self.categoria_ids:
            ws.write(4, 3, lista_categorias)

        # ****
        if not self.origen_ids:
            ws.write(5, 0, u"Todos los Origenes", header_left)
        else:
            ws.write(5, 0, u"Origenes:", header_left)
            origenes = ""
            for origen in self.origen_ids:
                origenes += origen.display_name + ','
            ws.write(5, 1, origenes)

        # ****
        if not self.destino_ids:
            ws.write(6, 0, u"Todos los Destinos", header_left)
        else:
            ws.write(6, 0, u"Destinos:", header_left)
            destinos = ""
            for destino in self.destino_ids:
                destinos += destino.display_name + ','
            ws.write(6, 1, destinos)

        fila += 10

        # **************
        # Escribo el titulo

        ws.write(fila, 0, u"Sector", title_ice_blue)
        ws.write(fila, 1, u"Fecha", title_ice_blue)
        ws.write(fila, 2, u"Categoria Interna", title_ice_blue)
        ws.write(fila, 3, u"CC Origen", title_ice_blue)
        ws.write(fila, 4, u"Centro Costo Origen", title_ice_blue)
        ws.write(fila, 5, u"Almacen Origen", title_ice_blue)
        ws.write(fila, 6, u"CC Destino", title_ice_blue)
        ws.write(fila, 7, u"Centro Costo Destino", title_ice_blue)
        ws.write(fila, 8, u"Almacen Destino", title_ice_blue)
        ws.write(fila, 9, u"Importe FIFO", title_ice_blue)
        ws.write(fila, 10, u"Importe Ult. Compra", title_ice_blue)
        ws.write(fila, 11, u"Cantidad", title_ice_blue)
        ws.write(fila, 12, u"Rubro del Producto", title_ice_blue)
        ws.write(fila, 13, u"Desc Rubro del Producto", title_ice_blue)
        ws.write(fila, 14, u"Rubro Consumo Producto", title_ice_blue)
        ws.write(fila, 15, u"Desc Rubro Consumo Producto", title_ice_blue)

        fila += 1

        consulta = """
                      SELECT  sector,
                              TO_CHAR(fecha, 'MM / yy') as fecha,
                               categoria_interna,
                              rubroentrada as RubroOrigen,
                              rubro_centro_entrada as CentroCostoOrigen,
                              Almacen_Origen,
                              rubrosalida as RubroDestino,
                              rubro_centro_salida as CentroCostoDestino,	
                              Almacen_Destino,                              
                              CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_fifo) * 1.02
                        ELSE sum(total_fifo)
              END as costo_fifo,
                              CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_ultima_compra) * 1.02
                        ELSE sum(total_ultima_compra)
              END as ultima_compra,
                            sum(product_qty) as product_qty ,
                              codigo as a , rubro as b,
                              codigo_consumo, rubro_consumo
                       FROM sp_consumos_mov_report(%(ffecha_i)s,%(ffecha_f)s,%(sector_ids)s,%(es_de_consumo)s,%(categoria_ids)s,%(origen_ids)s,%(destino_ids)s) """

        
        if self.sector_ids:
            sector_ids_str = json.dumps(self.sector_ids.ids).replace('[','').replace(']','')

        if self.categoria_ids:
            categoria_ids_str = json.dumps(self.categoria_ids.ids).replace('[','').replace(']','')
        
        if self.origen_ids:
            origen_ids_str = json.dumps(self.origen_ids.ids).replace('[','').replace(']','')

        if self.destino_ids:
            destino_ids_str = json.dumps(self.destino_ids.ids).replace('[','').replace(']','')


        vals = {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                             'ffecha_f': self.fecha_final + ' 23:59:59',
                             'sector_ids': sector_ids_str if self.sector_ids else '',
                             'categoria_ids': categoria_ids_str if self.categoria_ids else '' ,
                             'origen_ids': origen_ids_str if self.origen_ids else '',
                             'destino_ids': destino_ids_str if self. destino_ids else '',
                             'es_de_consumo':1 if self.solo_consumos else 0
                             }
        
        consulta += """ GROUP BY sector, TO_CHAR(fecha, 'MM / yy'),
                          categoria_interna,
                          RubroOrigen,
                          CentroCostoOrigen,
                          Almacen_Origen,
                          RubroDestino,
                          CentroCostoDestino,
                          product_qty, 
                          Almacen_Destino,
                          codigo,rubro,codigo_consumo, rubro_consumo
              ORDER BY TO_CHAR(fecha, 'MM / yy') """

        self.env.cr.execute(consulta, vals)

        resultado = self.env.cr.fetchall()
        # Escribo una linea por producto encontrado
        # La última columna es para el color
        for producto in resultado:
            fuente = Font()
            fuente.name = "Calibri"

            # if producto[-1]:
            #     fuente.colour_index = xlwt.Style.colour_map[producto[-1]]

            estilo = XFStyle()
            estilo.font = fuente

            # Escribo los datos de cada producto
            for columna, dato in enumerate(producto):
                if columna == 2:

                    categoria = self.env['product.category'].search([('name', '=', dato)])
                    rubro_codigo_gastos_code = categoria.property_account_expense_categ.code
                    rubro_codigo_gastos_name = categoria.property_account_expense_categ.name

                    if int(rubro_codigo_gastos_code) == 0:
                        rubro_codigo_gastos_code = ' '
                        rubro_codigo_gastos_name = ' '

                if (columna == 9) or (columna == 10) or (columna == 11):
                    ws.write(fila, columna, dato, lineas_estilo_num)
                else:
                    if (columna == 3) or (columna == 6):
                        ws.write(fila, columna, dato, lineas_estilo_num_int)
                    else:
                        ws.write(fila, columna, dato, lineas_estilo)
            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 25,
            1: 10,
            2: 25,
            3: 15,
            4: 20,
            5: 20,
            6: 15,
            7: 20,
            8: 20,
            9: 20,
            10: 20,
            11: 20,
            12: 15,
            13: 30,
            14: 60,
            15: 60,

        }

        for col in range(0, 33):
            ws.set_column(0, col, 15)


        wb.close()
        fp.seek(0)
        data = fp.read()
        fp.close()
        #data_to_save = base64.decodebytes(data)

        # fp = StringIO()
        # wb.close()
        # wb.save(fp)
        # fp.seek(0)
        # data = fp.read()
        # fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Consumos_Resumen.xlsx",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.consumos_pdf&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }


    @api.multi
    def action_detallado_producto(self):
        self.ensure_one()

        final = date(*map(int, self.fecha_final.split("-")))
        inicial = final - relativedelta(months=11)

        # Creo el libro Excel
        fp = BytesIO()
        wb = xlsxwriter.Workbook(fp)
        ws = wb.add_worksheet()


        #wb = Workbook(encoding='utf-8')
        #ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)

        # Estilos
        # # Estilos
        title_big = wb.add_format({'bold': True,'valign': 'top', 'font_size':12,'font_color':'#175785'})
        header = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal center'})
        title = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal left'})
        title_number = wb.add_format({'bold': True,'font_name':'Calibri','align': 'horizontal right','num_format':'#,##0.00;-#,##0.00;'})
        title_ice_blue = wb.add_format({'align': 'horizontal center','fg_color':'#74c4fc'})
        header_left = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left','bold': True})
        fecha = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal center','num_format':'DD/MM/YYYY'})

        lineas_estilo = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal left'})

        lineas_estilo_num_int = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '0'})

        lineas_estilo_num = wb.add_format(
            {'font_name': 'Calibri', 'align': 'horizontal right','num_format': '#.##0,0;-#.##0,0;'})

        fila = 0

        # Datos de la empresa y fecha de emision
        #ws.row(fila).height = 2 * 200
        ws.write(fila, fila, "Planilla Resumen por Producto", title_big)

        # ws.write(1, 0, u"Filtros", header_left)
        ws.write(2, 0, u"Rango de Fechas", header_left)
        ws.write(2, 1, u'Desde ' + self.fecha_inicial, fecha)
        ws.write(2, 2, u'Hasta ' + self.fecha_final, fecha)
       

        fila += 10

        # **************
        # Escribo el titulo
        #ws.write(fila, 0, u"Identificador", title_ice_blue)
        ws.write(fila, 0, u"Código", title_ice_blue)
        ws.write(fila, 1, u"Producto", title_ice_blue)
        ws.write(fila, 2, u"Cantidad", title_ice_blue)
        
        fila += 1

        consulta = """
                      SELECT  CodMSP,
                              product_template_name,
                              sum(product_qty) as cantidad
                       FROM sp_consumos_mov_report(%(ffecha_i)s,%(ffecha_f)s,%(sector_ids)s,%(es_de_consumo)s,%(categoria_ids)s,%(origen_ids)s,%(destino_ids)s) """

        
        if self.sector_ids:
            sector_ids_str = json.dumps(self.sector_ids.ids).replace('[','').replace(']','')

        if self.categoria_ids:
            categoria_ids_str = json.dumps(self.categoria_ids.ids).replace('[','').replace(']','')
        
        if self.origen_ids:
            origen_ids_str = json.dumps(self.origen_ids.ids).replace('[','').replace(']','')

        if self.destino_ids:
            destino_ids_str = json.dumps(self.destino_ids.ids).replace('[','').replace(']','')


        vals = {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                             'ffecha_f': self.fecha_final + ' 23:59:59',
                             'sector_ids': sector_ids_str if self.sector_ids else '',
                             'categoria_ids': categoria_ids_str if self.categoria_ids else '' ,
                             'origen_ids': origen_ids_str if self.origen_ids else '',
                             'destino_ids': destino_ids_str if self. destino_ids else '',
                             'es_de_consumo':1 if self.solo_consumos else 0
                             }
        
        consulta += """ GROUP BY product_template_name ,CodMSP"""

        self.env.cr.execute(consulta, vals)

        resultado = self.env.cr.fetchall()
        # Escribo una linea por producto encontrado
        # La última columna es para el color
        for producto in resultado:
            fuente = Font()
            fuente.name = "Calibri"

            # if producto[-1]:
            #     fuente.colour_index = xlwt.Style.colour_map[producto[-1]]

            estilo = XFStyle()
            estilo.font = fuente
            
            # Escribo los datos de cada producto
            for columna, dato in enumerate(producto):
            
                if (columna == 0) or (columna == 2):
                    ws.write(fila, columna, dato, lineas_estilo_num_int)
                else:
                    ws.write(fila, columna, dato, lineas_estilo)
            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 25,
            1: 10,
            2: 45,
            3: 15,
            4: 20,
            5: 20,
            6: 15,
            7: 20,
            8: 20,
            9: 20,
            10: 20,
            11: 20,
            12: 15,
            13: 30,
            14: 60,
            15: 60,

        }

        for col in range(0, 33):
            ws.set_column(0, col, 15)


        wb.close()
        fp.seek(0)
        data = fp.read()
        fp.close()
        #data_to_save = base64.decodebytes(data)

        # fp = StringIO()
        # wb.close()
        # wb.save(fp)
        # fp.seek(0)
        # data = fp.read()
        # fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Consumos_Resumen_por_producto.xlsx",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.consumos_pdf&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }
