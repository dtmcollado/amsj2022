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


class wizard(models.TransientModel):
    _name = "wizard.ultimas.facturas"
    sector_id = fields.Many2one('categoria', 'Sector')
    fecha_final = fields.Date('Fecha Fin', default=date.today())
    # tipo_facturas = fields.Selection([('pagas', 'Facturas Pagas'), ('validadas', 'Factura Validadas')], string="Seleccionar tipo de Facturas", default='pagas')
    binario = fields.Binary(string='guardo_archivo')
    archivo_nombre = fields.Char(string='')

    def modif_fecha(self, fecha):
        modif = time.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
        anio = time.strftime('%Y', modif)
        mes = time.strftime('%m', modif)
        dia = time.strftime('%d', modif)
        completo = datetime.date(int(anio), int(mes), int(dia))
        format_fecha = completo.strftime("%d-%m-%Y")
        return format_fecha

    @api.multi
    def action_export_validadas(self):
        self.ensure_one()

        # f_inicial = date(*map(int, self.fecha_inicial.split("-")))
        f_final = date(*map(int, self.fecha_final.split("-")))

        # f_inicial = f_inicial.strftime("%Y-%m-%d")
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

        # titulos
        ws.write(0, 0, "Tipo de Bien", title_lime)
        ws.write(0, 1, 'Código Artículo', title_lime)
        ws.write(0, 2, 'Nombre Articulo', title_lime)
        ws.write(0, 3, 'Fecha Contable', title_lime)
        ws.write(0, 4, 'Fecha Factura', title_lime)
        ws.write(0, 5, 'Código Proveedor', title_lime)
        ws.write(0, 6, 'Nombre Proveedor', title_lime)
        ws.write(0, 7, 'Nro. Factura', title_lime)
        ws.write(0, 8, 'Precio del Artículo', title_lime)
        ws.write(0, 9, 'Cantidad de unidades', title_lime)

        fila = 0

        sql = '''
                SELECT   
            CASE
                 WHEN pt."type" = 'product'  THEN 'Almacenable'
                 WHEN pt."type" = 'consu'  THEN 'Consumible'
                 WHEN pt."type" = 'service'  THEN 'Servicio' 
            END as Tipo_de_bien
             , p.default_code as Codigo_Articulo
             , p.name_template as nombre_producto 
             , po.date_invoice as Fecha_Contable
             , po.fecha_factura as Fecha_Factura
             , prov."codigoAMSJ" as Codigo_Proveedor
             , prov.display_name as Nombre_Proveedor
             , po.supplier_invoice_number as Nro_Factura
             , pol.price_unit::numeric(16,2)
             , pol.quantity   
             , pc.name as categoria          
             FROM account_invoice po
                 JOIN res_partner prov ON prov.id = po.partner_id 
                 JOIN account_invoice_line pol ON po.id = pol.invoice_id
                 JOIN product_product p ON p.id = pol.product_id
                 JOIN product_template pt ON pt.id = p.product_tmpl_id
                 JOIN product_category pc ON pc.id = pt.categ_id
                 JOIN ( SELECT pol_1.product_id,
                        max(po_1.date_invoice) AS date_invoice
                       FROM account_invoice po_1
                         JOIN account_invoice_line pol_1 ON po_1.id = pol_1.invoice_id
                      WHERE po_1.state::text <> 'draft'::text and po_1.date_invoice <= %(fecha_hasta)s
                      GROUP BY pol_1.product_id) d ON d.product_id = pol.product_id AND d.date_invoice = po.date_invoice
              WHERE po.state::text <> 'draft'::text
              and po.date_invoice <=   DATE %(fecha_hasta)s  and sector = %(sector)s;
        '''

        self.env.cr.execute(sql,
                            {'fecha_hasta': self.fecha_final, 'sector': self.sector_id.id}
                            )
        resultado = self.env.cr.fetchall()

        if len(resultado) > 0:
            estilo = None
            for res in resultado:
                fila += 1

                if fila % 2 == 0:
                    estilo = lineas_estilo_gris

                else:
                    estilo = lineas_estilo

                ws.write(fila, 0, res[0], estilo)
                ws.write(fila, 1, res[1], estilo)
                ws.write(fila, 2, res[2], estilo)
                ws.write(fila, 3, self.modif_fecha(res[3]), estilo)
                if res[4]:
                    ws.write(fila, 4, self.modif_fecha(res[4]), estilo)
                else:
                    ws.write(fila, 4, self.modif_fecha(res[3]), estilo)
                ws.write(fila, 5, res[5], estilo)
                ws.write(fila, 6, res[6], estilo)
                ws.write(fila, 7, res[7], estilo)
                ws.write(fila, 8, res[8], estilo)
                ws.write(fila, 9, res[9], estilo)

            fila += 1
            ws.write(fila, 0, '', lineas_estilo)

        anchos = {
            0: 10,
            1: 10,
            2: 45,
            3: 15,
            4: 15,
            5: 15,
            6: 35,
            7: 15,
            8: 15,
            9: 15,
        }

        for col in range(0, len(anchos) + 3):
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
            'archivo_nombre': "Reporte_Facturas.xlsx",
            'binario': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.ultimas.facturas&field=binario&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }


class wizard_historico(models.TransientModel):
    _name = "wizard.historico.facturas"
    sector_id = fields.Many2one('categoria', 'Sector')
    fecha_inicial = fields.Date('Fecha Inicial', default=date.today())
    fecha_final = fields.Date('Fecha Fin', default=date.today())
    # tipo_facturas = fields.Selection([('pagas', 'Facturas Pagas'), ('validadas', 'Factura Validadas')], string="Seleccionar tipo de Facturas", default='pagas')
    binario = fields.Binary(string='guardo_archivo')
    archivo_nombre = fields.Char(string='')

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

        wb = Workbook(encoding='utf8')
        ws = wb.add_sheet('Hoja 1', cell_overwrite_ok=True)

        # titulos
        ws.write(0, 0, "Tipo de Bien", title_lime)
        ws.write(0, 1, 'Categoria', title_lime)
        ws.write(0, 2, 'Código Artículo', title_lime)
        ws.write(0, 3, 'Nombre Articulo', title_lime)
        ws.write(0, 4, 'Fecha Contable', title_lime)
        ws.write(0, 5, 'Fecha Factura', title_lime)
        ws.write(0, 6, 'Código Proveedor', title_lime)
        ws.write(0, 7, 'Nombre Proveedor', title_lime)
        ws.write(0, 8, 'Nro. Factura', title_lime)
        ws.write(0, 9, 'Precio del Artículo', title_lime)
        ws.write(0, 10, 'Cantidad de unidades', title_lime)


        fila = 0

        sql = '''
           SELECT   
            CASE
                 WHEN pt."type" = 'product'  THEN 'Almacenable'
                 WHEN pt."type" = 'consu'  THEN 'Consumible'
                 WHEN pt."type" = 'service'  THEN 'Servicio' 
            END as Tipo_de_bien
              , pc.name as categoria    
             , p.default_code as Codigo_Articulo
             , p.name_template as nombre_producto  
             , ai.date_invoice as Fecha_Contable
             , ai.fecha_factura as Fecha_Factura
             , prov."codigoAMSJ" as Codigo_Proveedor
             , prov.display_name as Nombre_Proveedor
             , ai.supplier_invoice_number as Nro_Factura
             , ail.price_unit::numeric(16,2)
             , ail.quantity     
             
             FROM account_invoice ai
                 JOIN res_partner prov ON prov.id = ai.partner_id 
                 JOIN account_invoice_line ail ON ai.id = ail.invoice_id and NOT lower(ail.name) like 'redondeo'::text
                 JOIN product_product p ON p.id = ail.product_id
                 JOIN product_template pt ON pt.id = p.product_tmpl_id
                 JOIN product_category pc ON pc.id = pt.categ_id
               WHERE ai.state::text <> 'draft'::text 
              and ai.date_invoice >= DATE %(fecha_desde)s and ai.date_invoice <= DATE %(fecha_hasta)s 
               and sector = %(sector)s;
        '''
        #   cr.execute('SELECT digits FROM decimal_precision WHERE name like %s',('Account',))
        #   and NOT lower(ail.name) like '%redondeo%'::text
        #   AND ai.date_invoice >= DATE %(fecha_desde)s AND ai.date_invoice <= DATE %(fecha_hasta)s
        #   AND (ai.date_invoice >= %(fecha_desde)s and ai.date_invoice =< %(fecha_hasta)s)
        #     'fecha_desde': self.fecha_inicial,
        #                              'fecha_hasta': self.fecha_final,

        # {'fecha_desde': self.fecha_inicial,
        #  'fecha_hasta': self.fecha_final,
        #  'sector': self.sector_id.id}

        self.env.cr.execute(sql,
                            {'fecha_desde': self.fecha_inicial, 'fecha_hasta': self.fecha_final,
                             'sector': self.sector_id.id})

        resultado = self.env.cr.fetchall()

        if len(resultado) > 0:
            estilo = None
            for res in resultado:
                fila += 1

                if fila % 2 == 0:
                    estilo = lineas_estilo_gris

                else:
                    estilo = lineas_estilo

                ws.write(fila, 0, res[0], estilo)
                ws.write(fila, 1, res[1], estilo)
                ws.write(fila, 2, res[2], estilo)
                ws.write(fila, 3, res[3], estilo)
                ws.write(fila, 4, self.modif_fecha(res[4]), estilo)
                if res[5]:
                    ws.write(fila, 5, self.modif_fecha(res[5]), estilo)
                else:
                    ws.write(fila, 5, self.modif_fecha(res[4]), estilo)

                ws.write(fila, 6, res[6], estilo)
                ws.write(fila, 7, res[7], estilo)
                ws.write(fila, 8, res[8], estilo)
                ws.write(fila, 9, res[9], estilo)
                ws.write(fila, 10, res[10], estilo)

            fila += 1
            ws.write(fila, 0, '', lineas_estilo)

        anchos = {
            0: 10,
            1: 10,
            2: 45,
            3: 15,
            4: 15,
            5: 15,
            6: 35,
            7: 15,
            8: 15,
            9: 15,
            10: 20,
        }

        for col in range(0, len(anchos) + 3):
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
            'archivo_nombre': "Historico_Facturas.xlsx",
            'binario': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.historico.facturas&field=binario&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }
