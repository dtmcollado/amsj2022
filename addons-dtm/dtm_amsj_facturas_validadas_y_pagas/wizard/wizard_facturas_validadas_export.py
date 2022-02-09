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


class wizard_facturas_validadas_export(models.TransientModel):
    _name = "wizard.facturas.validadas.export"

    sector_id = fields.Many2one('categoria', 'Sector', select=True)
    fecha_inicial = fields.Date('Fecha Contable Inicio', default=date.today().replace(day=1))
    fecha_final = fields.Date('Fecha Contable Fin', default=date.today())
    tipo_facturas = fields.Selection([('pagas', 'Facturas Pagas'), ('validadas', 'Factura Validadas')], string="Seleccionar tipo de Facturas", default='pagas')
    binario = fields.Binary(string='guardo_archivo')
    archivo_nombre = fields.Char(string='')
    nro_factura = fields.Char(string='Nro Factura')
    facturas_ids = fields.Many2many('account.invoice','account_invoice_fact_valid_rel', string='Facturas')
    bandera = fields.Boolean(string='Existe?')
    buscar_por_nro = fields.Boolean(string='Buscar por Nro de Factura')
    buscar_por_prove = fields.Boolean(string='Buscar por Proveedor')
    proveedor_ids = fields.Many2one('res.partner', 'Proveedor', select=True)

    @api.multi
    @api.onchange('nro_factura')
    def _onchange_nro_factura(self):
        if self.nro_factura:
            factura_rec=self.env['account.invoice'].search([('supplier_invoice_number','=',self.nro_factura.upper())])
            fact_list = []
            self.bandera = False
            if factura_rec:
                for i in factura_rec:
                    # self.employees_id = [(5,False,False)]
                    # for hr in self.employees_id:
                    fact_list.append((4,i.id,False))

                    self.facturas_ids=fact_list
                    #la banderita le da color para saber al usuario que puso bien el nro de empleado
                    self.bandera = True
                    self.nro_factura=False



    def modif_fecha(self, fecha):
        modif = time.strptime(fecha,DEFAULT_SERVER_DATE_FORMAT)
        anio = time.strftime('%Y', modif)
        mes = time.strftime('%m', modif)
        dia = time.strftime('%d', modif)
        completo=datetime.date(int(anio),int(mes),int(dia))
        format_fecha = completo.strftime("%d-%m-%Y")
        return format_fecha



    @api.multi
    def action_export_validadas(self):
        self.ensure_one()

        f_inicial = date(*map(int, self.fecha_inicial.split("-")))
        f_final = date(*map(int, self.fecha_final.split("-")))

        f_inicial = f_inicial.strftime("%Y-%m-%d")
        f_final = f_final.strftime("%Y-%m-%d")
        #filtra el estado en las validadas...... en las facturas pagadas que este pagada

        title_lime = easyxf('pattern: pattern solid, fore_colour lime;font: bold 1;')
        title_plan = easyxf('pattern: pattern solid, fore_colour light_green;font: bold 1;')
        title_real = easyxf('pattern: pattern solid, fore_colour gold;font: bold 1;')
        title_calculos = easyxf('pattern: pattern solid, fore_colour periwinkle;font: bold 1;')
        lineas_estilo = easyxf('font: name Calibri; alignment: horizontal left')
        lineas_estilo_gris = easyxf('pattern:  pattern solid, fore_colour gray25; font: name Calibri; alignment: horizontal left;')
        lineas_hs=easyxf('font: name Calibri; alignment: horizontal left;font: bold 1;')

        wb = Workbook(encoding='utf8')
        ws = wb.add_sheet('Hoja 1', cell_overwrite_ok=True)


        #titulos
        ws.write(0,0,"Cliente",title_lime)
        ws.write(0,1,'Nº de Factura',title_lime)
        ws.write(0,2,'Fecha Contable',title_lime)
        ws.write(0,3,'Fecha de Vencimiento',title_lime)
        ws.write(0,4,'Total',title_lime)


        fila=0
        sql = ''
        if self.tipo_facturas == "pagas":
            sql=''' 
                SELECT rp.name, ai.supplier_invoice_number, ai.date_invoice, ai.date_due, ai.amount_total 
                    from account_invoice ai 
                    inner join res_partner rp on rp.id = ai.partner_id
                where ai.state = 'paid' and  sector = %(sector_id)s 
                and  ai.date_invoice  >= DATE %(fecha_desde)s  and
                  ai.date_invoice <= DATE %(fecha_hasta)s
                  
            '''
            if self.facturas_ids and self.buscar_por_nro:
                #Si busca por nro de factura no busca por fecha de facturas
                sql=''' 
                SELECT rp.name, ai.supplier_invoice_number, ai.date_invoice, ai.date_due, ai.amount_total 
                    from account_invoice ai 
                    inner join res_partner rp on rp.id = ai.partner_id
                where ai.state = 'paid' and  sector = %(sector_id)s 
                         
                '''
                ids=''
                sin_coma=False
                for x in self.facturas_ids:
                    if sin_coma== False:
                        ids=ids + str(x.id)
                        sin_coma = True
                    else:
                        ids=ids+','+ str(x.id)
                sql=sql+' and ai.id in ({ids})'.format(ids=ids)

            if self.buscar_por_prove and self.proveedor_ids:
                ids_prov = str(self.proveedor_ids.id)
                sql=sql+' and ai.partner_id in ({ids})'.format(ids=ids_prov)

        else:
            sql=''' 
                SELECT rp.name, ai.supplier_invoice_number, ai.date_invoice, ai.date_due, ai.amount_total 
                    from account_invoice ai 
                    inner join res_partner rp on rp.id = ai.partner_id
                where ai.state = 'open' and  sector = %(sector_id)s  and 
                 ai.date_invoice  >= DATE %(fecha_desde)s  and
                  ai.date_invoice <= DATE %(fecha_hasta)s
                '''
            if self.facturas_ids and self.buscar_por_nro:
                #Si busca por nro de factura no busca por fecha de facturas
                sql=''' 
                SELECT rp.name, ai.supplier_invoice_number, ai.date_invoice, ai.date_due, ai.amount_total 
                    from account_invoice ai 
                    inner join res_partner rp on rp.id = ai.partner_id
                where ai.state = 'open' and  sector = %(sector_id)s 
                '''
                ids=''
                sin_coma=False
                for x in self.facturas_ids:
                    if sin_coma== False:
                        ids=ids + str(x.id)
                        sin_coma = True
                    else:
                        ids=ids+','+ str(x.id)
                sql=sql+' and ai.id in ({ids})'.format(ids=ids)

            if self.buscar_por_prove and self.proveedor_ids:
                ids_prov = str(self.proveedor_ids.id)
                sql=sql+' and ai.partner_id in ({ids})'.format(ids=ids_prov)



        sql=sql+'order by ai.date_invoice'

        self.env.cr.execute(sql,
                            {'fecha_desde': self.fecha_inicial,
                             'fecha_hasta': self.fecha_final,
                             'sector_id': self.sector_id.id}
                            )
        resultado = self.env.cr.fetchall()

        if len(resultado)>0:
                estilo=None
                for res in resultado:
                    fila+=1

                    if fila%2==0:
                        estilo=lineas_estilo_gris

                    else:
                        estilo=lineas_estilo

                    ws.write(fila,0,res[0],estilo)
                    ws.write(fila,1,res[1],estilo)
                    ws.write(fila,2,self.modif_fecha(res[2]),estilo)
                    ws.write(fila,3,self.modif_fecha(res[3]),estilo)
                    ws.write(fila,4,res[4],estilo)


                fila+=1
                ws.write(fila,0,'',lineas_estilo)

        anchos = {
                0: 35,
                1: 22,
                2: 15,
                3: 15,
                4: 15,
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
            'archivo_nombre': "Reporte_Facturas.xlsx",
            'binario': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=wizard.facturas.validadas.export&field=binario&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }

