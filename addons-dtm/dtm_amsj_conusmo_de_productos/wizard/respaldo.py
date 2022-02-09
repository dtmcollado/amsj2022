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



class wizard(models.TransientModel):
    _name = "wizard.consumos_pdf"


    @api.multi
    def get_domain_sector(self):
        # 18
        # 19
        return [('id', '<>',17 )]


    fecha_inicial = fields.Date('Begin date', default=date.today().replace(day=1))
    fecha_final = fields.Date('End date', default=date.today())

    # sector_id = fields.Many2one('categoria', 'Sector')
    sector_ids = fields.Many2many(comodel_name='categoria',
                                              string="Sectores" , domain=get_domain_sector
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




    almacen_origen_ids = fields.Many2many(comodel_name='stock.warehouse',string='Almacenes')
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
                        location_ids.append(loc.id)
                    for loc1 in loc.child_ids:
                        if not loc1.scrap_location:
                            location_ids.append(loc1.id)
                        for loc2 in loc1.child_ids:
                            if not loc2.scrap_location:
                                location_ids.append(loc2.id)
                            for loc3 in loc2.child_ids:
                                if not loc3.scrap_location:
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

    @api.one
    @api.constrains('fecha_desde', 'fecha_hasta')
    def _control_fechas(self):
        if self.fecha_inicial > self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

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

        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;pattern: pattern solid, fore_colour pale_blue;')
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
        title_ice_blue = easyxf('pattern: pattern solid, fore_colour ice_blue;font: bold 1 ,height 230; alignment: horizontal center')
        lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
        lineas_estilo_gris = easyxf('pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
        lineas_estilo_num = easyxf('font: name Calibri; alignment: horizontal left', num_format_str='#,##0.00;-#,##0.00;')
        lineas_estilo_gris_num = easyxf('pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;', num_format_str='#,##0.00;-#,##0.00;')

        fila = 0

        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        ws.write_merge(fila, fila, 3, 7, "Planilla Consumos", title_big)

        # ws.write(1, 0, u"Filtros", header_left)
        ws.write(2, 0, u"Rango de Fechas", header_left)
        ws.write(2, 1, u'Desde ' + self.fecha_inicial,fecha)
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
            ws.write(3, 3,lista_sectores)
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
            ws.write(4, 3,lista_categorias)

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
        ws.write(fila, 1, u"Categoria Interna", title_ice_blue)
        ws.write(fila, 2, u"Código", title_ice_blue)
        ws.write(fila, 3, u"Producto", title_ice_blue)
        ws.write(fila, 4, u"SemaUcor", title_ice_blue)
        ws.write(fila, 5, u"FTM", title_ice_blue)
        ws.write(fila, 6, u"Codigo GeoSalud", title_ice_blue)
        ws.write(fila, 7, u"Principio_Activo", title_ice_blue)
        ws.write(fila, 8, u"Familia", title_ice_blue)
        ws.write(fila, 9, u"Grupo", title_ice_blue)
        ws.write(fila, 10, u"SubGrupo", title_ice_blue)
        ws.write(fila, 11, u"Forma Farmaceutica", title_ice_blue)
        ws.write(fila, 12, u"Cantidad", title_ice_blue)
        ws.write(fila, 13, u"Almacen Origen", title_ice_blue)
        ws.write(fila, 14, u"Ubicación Origen", title_ice_blue)
        ws.write(fila, 15, u"Centro Costo", title_ice_blue)
        ws.write(fila, 16, u"Almacen Destino", title_ice_blue)
        ws.write(fila, 17, u"Ubicación Destino", title_ice_blue)
        ws.write(fila, 18, u"Centro Costo", title_ice_blue)
        ws.write(fila, 19, u"Importe FIFO", title_ice_blue)
        ws.write(fila, 20, u"Importe Ult. Compra", title_ice_blue)
        ws.write(fila, 21, u"Fecha", title_ice_blue)
        ws.write(fila, 22, u"Rubro Categoria Gastos", title_ice_blue)
        ws.write(fila, 23, u"Rubro Categoria Ingresos", title_ice_blue)

        fila += 1

        # ****************
        # meses_cadena = meses_cadena[:-1]  # Le quito última la coma para que
        # quede más intuitivo al ejecutar la
        # función sql
        # Hago el query en la base
        # consulta = """select
        #           sector ,
        #            categoria_interna,
        #            CodMSP,
        #            product_template_name,
        #            sema_ucor,
        #            ftm,
        #            codigo_geosalud,
        #            'NA' as p_activo,
        #            familia,
        #            grupo,
        #            subgrupo,
        #            forma_farmaceutica,
        #            product_qty,
        #            Almacen_Origen,
        #            origen,
        #            rubro_centro_entrada,
        #            Almacen_Destino,
        #            destino,
        #            rubro_centro_salida,
        #            total_fifo as costo_fifo,
        #            total_ultima_compra as costo_compra,
        #            TO_CHAR(fecha :: DATE, 'dd/mm/yyyy'),
        #            'Rubro Categoria Gastos' as RubroCategoriaGastos,
        #            'Rubro Categoria Ingresos' as RubroCategoriaIngresos,
        #            product_template_id
        #                 FROM consumos_report
        #                 WHERE (fecha >= DATE %(ffecha_i)s and
        #                         fecha <= DATE %(ffecha_f)s) """



        consulta = """select
                          sector ,
                           categoria_interna,
                           CodMSP,
                           product_template_name,
                           sema_ucor,
                           ftm,
                           codigo_geosalud,
                           'NA' as p_activo,
                           familia,
                           grupo,
                           subgrupo,
                           forma_farmaceutica,
                           product_qty,
                           Almacen_Origen,
                           origen,
                           rubro_centro_entrada,
                           Almacen_Destino,
                           destino,
                           rubro_centro_salida,
                           total_fifo as costo_fifo,
                           total_ultima_compra as costo_compra,
                           TO_CHAR(fecha :: DATE, 'dd/mm/yyyy'),
                           'Rubro Categoria Gastos' as RubroCategoriaGastos,
                           'Rubro Categoria Ingresos' as RubroCategoriaIngresos,
                           product_template_id
                                FROM sp_consumos_report(%(ffecha_i)s,%(ffecha_f)s) """

        if self.sector_ids:
            consulta += """ where sector_id in %(sector_ids)s"""
        else:
            consulta += """ where """

        if self.categoria_ids:
            consulta += """ and categoria_interna_id in %(categoria_ids)s"""
        if self.origen_ids:
            consulta += """ and origen_id in %(origen_ids)s"""
        if self.destino_ids:
            consulta += """ and destino_id in %(destino_ids)s"""

        if not self.todos_FTM:
            if self.FTM:
                consulta += """ and FTM = 'True' """
            else:
                consulta += """ and FTM = 'False' """

        consulta += " ORDER BY fecha"

        self.env.cr.execute(consulta,
                                {'ffecha_i': self.fecha_inicial,
                                 'ffecha_f': self.fecha_final,
                                 'sector_ids': tuple(self.sector_ids.ids),
                                 'categoria_ids': tuple(self.categoria_ids.ids),
                                 'origen_ids': tuple(self.origen_ids.ids),
                                 'destino_ids': tuple(self.destino_ids.ids)
                                 })


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
                if columna == 24:
                    producto_id = int(dato)
                    producto_obj = self.env['product.template'].search([('id', '=', producto_id)])
                    rubro_codigo_gastos = producto_obj.categ_id.property_account_expense_categ.display_name

                    rubro_codigo_compras = producto_obj.categ_id.property_account_income_categ.display_name
                    if fila%2 == 0:
                        ws.write(fila, 22, rubro_codigo_gastos, lineas_estilo_gris)
                        ws.write(fila, 23, rubro_codigo_compras, lineas_estilo_gris)
                    else:
                        ws.write(fila, 22, rubro_codigo_gastos, lineas_estilo)
                        ws.write(fila, 23, rubro_codigo_compras, lineas_estilo)

                if columna in (4, 5):
                    if dato:
                        dato = 'X'
                    else:
                        dato = ' '

                if not columna == 24:

                    if fila%2 == 0:
                        ws.write(fila, columna, dato,lineas_estilo_gris_num)
                    else:
                        ws.write(fila, columna, dato,lineas_estilo_num)




            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 15,
            1: 15,
            2: 10,
            3: 35,
            4: 10,
            5: 10,
            6: 15,
            7: 35,
            8: 35,
            9: 35,
            10: 25,
            11: 25,
            12: 10,
            13: 10,
            14: 35,
            15: 10,
            16: 35,
            17: 25,
            18: 15,
            19: 15,
            20: 15,
            21: 15,
        }

        for col in range(0,21):
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
            'archivo_nombre': "Compras.xls",
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

        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;pattern: pattern solid, fore_colour pale_blue;')
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
        title_ice_blue = easyxf('pattern: pattern solid, fore_colour ice_blue;font: bold 1 ,height 230; alignment: horizontal center')
        lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
        lineas_estilo_num = easyxf('font: name Calibri; alignment: horizontal left', num_format_str='#,##0.00;-#,##0.00;')
        lineas_estilo_gris = easyxf('pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
        lineas_estilo_gris_num = easyxf('pattern: pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;', num_format_str='#,##0.00;-#,##0.00;')

        fila = 0

        # Datos de la empresa y fecha de emision
        ws.row(fila).height = 2 * 200
        ws.write_merge(fila, fila, 3, 7, "Planilla Consumos Resumen", title_big)

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
            ws.write(3, 3, lista_sectores)
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
        ws.write(fila, 1, u"Categoria Interna", title_ice_blue)
        ws.write(fila, 2, u"Producto", title_ice_blue)
        ws.write(fila, 3, u"Familia", title_ice_blue)
        ws.write(fila, 4, u"Grupo", title_ice_blue)
        ws.write(fila, 5, u"SubGrupo", title_ice_blue)
        ws.write(fila, 6, u"Cantidad", title_ice_blue)
        ws.write(fila, 7, u"Almacen Origen", title_ice_blue)
        ws.write(fila, 8, u"Ubicación Origen", title_ice_blue)
        ws.write(fila, 9, u"Centro Costo", title_ice_blue)
        ws.write(fila, 10, u"Almacen Destino", title_ice_blue)
        ws.write(fila, 11, u"Ubicación Destino", title_ice_blue)
        ws.write(fila, 12, u"Centro Costo", title_ice_blue)
        ws.write(fila, 13, u"Importe FIFO", title_ice_blue)
        ws.write(fila, 14, u"Importe Ult. Compra", title_ice_blue)
        ws.write(fila, 15, u"Rubro Categoria Gastos", title_ice_blue)
        ws.write(fila, 16, u"Rubro Categoria Ingresos", title_ice_blue)

        fila += 1


        consulta = """
                            select 
                               sector ,
                               categoria_interna,
                               product_template_name,
                               familia,
                               grupo,
                               subgrupo,
                               sum(product_qty) as cantidad,
                               Almacen_Origen,
                               origen,
                               rubro_centro_entrada,
                               Almacen_Destino,
                               destino,
                               rubro_centro_salida,
                               sum(total_fifo) as costo_fifo,
                               sum(total_ultima_compra) as costo_compra,
                               'Rubro Categoria Gastos' as RubroCategoriaGastos,
                               'Rubro Categoria Ingresos' as RubroCategoriaIngresos,
                               product_template_id
                        FROM sp_consumos_report(%(ffecha_i)s,%(ffecha_f)s)
                        
        """



        if self.sector_ids:
            consulta += """ where sector_id in %(sector_ids)s"""
        else:
            consulta += """ where """

        if self.categoria_ids:
            consulta += """ and categoria_interna_id in %(categoria_ids)s"""
        if self.origen_ids:
            consulta += """ and origen_id in %(origen_ids)s"""
        if self.destino_ids:
            consulta += """ and destino_id in %(destino_ids)s"""

        if not self.todos_FTM:
            if self.FTM:
                consulta += """ and FTM = 'True' """
            else:
                consulta += """ and FTM = 'False' """

        consulta += """ GROUP BY sector ,    categoria_interna,
                               CodMSP,  product_template_name,
                               sema_ucor, ftm,  codigo_geosalud,
                               familia, grupo, subgrupo,
                               forma_farmaceutica,                   
                               Almacen_Origen, origen, rubro_centro_entrada,
                               Almacen_Destino, destino,
                               rubro_centro_salida,product_template_id; """

        self.env.cr.execute(consulta,
                            {'ffecha_i': self.fecha_inicial,
                             'ffecha_f': self.fecha_final,
                             'sector_ids': tuple(self.sector_ids.ids),
                             'categoria_ids': tuple(self.categoria_ids.ids),
                             'origen_ids': tuple(self.origen_ids.ids),
                             'destino_ids': tuple(self.destino_ids.ids)
                             })

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
                if columna == 17:
                    producto_id = int(dato)
                    producto_obj = self.env['product.template'].search([('id', '=', producto_id)])
                    rubro_codigo_gastos = producto_obj.categ_id.property_account_expense_categ.display_name

                    rubro_codigo_compras = producto_obj.categ_id.property_account_income_categ.display_name
                    if fila%2 == 0:
                        ws.write(fila, 15, rubro_codigo_gastos, lineas_estilo_gris)
                        ws.write(fila, 16, rubro_codigo_compras, lineas_estilo_gris)
                    else:
                        ws.write(fila, 15, rubro_codigo_gastos, lineas_estilo)
                        ws.write(fila, 16, rubro_codigo_compras, lineas_estilo)


                if not columna == 17:
                    if fila%2 == 0:
                        ws.write(fila, columna, dato, lineas_estilo_gris_num)
                    else:
                        ws.write(fila, columna, dato, lineas_estilo_num)

            #         ws.write(fila, 16, u"Rubro Categoria Ingresos", header_left)

            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 15,
            1: 30,
            2: 35,
            3: 25,
            4: 35,
            5: 20,
            6: 10,
            7: 10,
            8: 15,
            9: 15,
            10: 20,
            11: 15,
            12: 15,
            13: 15,
            14: 15,
            15: 20,
            16: 20,
            17: 20,

        }

        for col in range(0, 20):
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
            'archivo_nombre': "Consumos.xls",
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


wizard()
