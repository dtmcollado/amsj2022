# -*- encoding: utf-8 -*-
from operator import itemgetter
from openerp.exceptions import ValidationError, Warning
import json


def validate_that_has_report_data():
    raise ValidationError(
        u"No se encuentran facturas a conformar para el período seleccionado")


def _datos_reporte_compras(self):
    list_qweb = []
    dict_prov = {}

    consulta = """
          select ai.date_invoice , rp.display_name , 
          CASE WHEN ai."type" = 'in_refund' THEN 'Nota de Crédito'
               WHEN ai."type" = 'in_invoice' THEN 'Factura'
                   ELSE '------' END
                   AS tipo
                    , ai.supplier_invoice_number  ,  ai.amount_total
          from account_invoice ai
           inner join res_partner rp on rp.id = ai.partner_id  
          where ai.sector in %(sector_ids)s and ai."type" in ('in_refund','in_invoice') and state = 'paid' 
          and ai.write_date >= DATE %(ffecha_i)s and ai.write_date <= DATE %(ffecha_f)s
          order by rp.display_name,ai.supplier_invoice_number;
          
                  """
    self.env.cr.execute(consulta,
                        {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                         'ffecha_f': self.fecha_final + ' 23:59:59',
                         'sector_ids': tuple(self.sector_ids.ids),

                         })

    resultado = self.env.cr.fetchall()
    totalCompra = 0

    for tupla in resultado:

        if tupla[2] == 'Factura':
            importe_linea = float(tupla[4])
        else:
            importe_linea = float(tupla[4]) * -1

        totalCompra += importe_linea

        list_qweb.append(
            {
                'fecha': tupla[0],
                'proveedor': tupla[1],
                'tipo': tupla[2],
                'numero': tupla[3],
                'importe': importe_linea,

            })

    list_qweb.append(
        {
            'fecha': ' ',
            'proveedor': 'TOTAL COMPRA DE BIENES DE CONSUMOS',
            'tipo': '',
            'numero': '',
            'importe': totalCompra

        })

    return list_qweb


def _datos_reporte_compras_contable(self):
    list_qweb = []
    dict_prov = {}

    consulta = """
          select ai.fecha_factura , ai.date_invoice , rp.display_name , 
          CASE WHEN ai."type" = 'in_refund' THEN 'Nota de Crédito'
               WHEN ai."type" = 'in_invoice' THEN 'Factura'
                   ELSE '------' END
                   AS tipo
                    , ai.supplier_invoice_number  ,  ai.amount_total
          from account_invoice ai
           inner join res_partner rp on rp.id = ai.partner_id  
          where ai.sector in %(sector_ids)s and ai."type" in ('in_refund','in_invoice') and state = 'paid' 
          and ai.date_invoice >= DATE %(ffecha_i)s and ai.date_invoice <= DATE %(ffecha_f)s
          order by rp.display_name,ai.supplier_invoice_number;

                  """
    self.env.cr.execute(consulta,
                        {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                         'ffecha_f': self.fecha_final + ' 23:59:59',
                         'sector_ids': tuple(self.sector_ids.ids),

                         })

    resultado = self.env.cr.fetchall()
    totalCompra = 0

    for tupla in resultado:

        if tupla[3] == 'Factura':
            importe_linea = float(tupla[5])
        else:
            importe_linea = float(tupla[5]) * -1

        totalCompra += importe_linea

        list_qweb.append(
            {
                'fecha': tupla[0],
                'fecha_factura': tupla[1],
                'proveedor': tupla[2],
                'tipo': tupla[3],
                'numero': tupla[4],
                'importe': importe_linea,

            })

    list_qweb.append(
        {
            'fecha': ' ',
            'proveedor': 'TOTAL COMPRA DE BIENES DE CONSUMOS',
            'tipo': '',
            'numero': '',
            'importe': totalCompra

        })

    return list_qweb


def _datos_reporte(self):
    list_qweb = []
    dict_prov = {}


    consulta = """
                 SELECT  categoria_interna,   CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_fifo) * 1.02
                        ELSE sum(total_fifo)
                          END as costo_fifo,
                              CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_ultima_compra) * 1.02
                        ELSE sum(total_ultima_compra) 
              END as ultima_compra   , categoria_interna_id
                      FROM sp_consumos_mov_report(%(ffecha_i)s,%(ffecha_f)s,%(sector_ids)s,%(es_de_consumo)s,%(categoria_ids)s,%(origen_ids)s,%(destino_ids)s) """


    consulta += """ GROUP BY sector,
                          categoria_interna , categoria_interna_id;
                          
			              
                 """
    consumo = 0
    origen_ids_str = ''
    sector_ids_str = ''
    categoria_ids_str = ''
    destino_ids_str = ''

    if self.sector_ids:
        sector_ids_str = json.dumps(self.sector_ids.ids).replace('[','').replace(']','')
        if self.sector_ids[0].id == 17:
          consumo = 1
        if self.sector_ids[0].id == 18:
          origen_ids_str = "520,522,524,521,523"

        if self.sector_ids[0].id == 19:
          origen_ids_str = "439,518,442,441,443,1021"


    vals = {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                         'ffecha_f': self.fecha_final + ' 23:59:59',
                         'sector_ids': sector_ids_str,
                         'categoria_ids': categoria_ids_str,
                         'origen_ids': origen_ids_str,
                         'destino_ids': destino_ids_str,
                         'es_de_consumo': consumo
                         }
    
    self.env.cr.execute(consulta, vals)

    resultado = self.env.cr.fetchall()
    totalCompra = 0
    totalFifo = 0
    for tupla in resultado:
        categoria = self.env['product.category'].search([('id', '=', tupla[3])])
        rubro_codigo_gastos_code = categoria.property_account_expense_categ.code
        rubro_codigo_gastos_name = categoria.property_account_expense_categ.name

        totalCompra += float(tupla[2])
        totalFifo += float(tupla[1])

        if (not categoria) :
            # or rubro_codigo_gastos_code == '220000':
            rubro_codigo_gastos_code = '- SIN DEFINIR -'
            rubro_codigo_gastos_name = tupla[0]

        list_qweb.append(
            {
                'rubro': rubro_codigo_gastos_code,
                'categoria': rubro_codigo_gastos_name,
                'compra': tupla[2],
                'fifo': tupla[1],

            })



    list_qweb.append(
        {
            'rubro': ' ',
            'categoria': 'TOTAL DE BIENES',
            'compra': totalCompra,
            'fifo':     totalFifo,

        })

    return list_qweb


def _datos_reporte_contabilidad(self):
    list_qweb = []
    dict_prov = {}

    consulta = """
                 SELECT  categoria_interna,   CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_fifo) * 1.02
                        ELSE sum(total_fifo)
                          END as costo_fifo,
                              CASE WHEN categoria_interna = 'MEDICAMENTOS' THEN sum(total_ultima_compra) * 1.02
                        ELSE sum(total_ultima_compra)
              END as ultima_compra   
                      FROM sp_consumos_mov_report(%(ffecha_i)s,%(ffecha_f)s)
    """

    # filtros
    if self.sector_ids:
        if self.sector_ids[0].id == 17:
            consulta += """ where es_de_consumo = 1 and origen_id <> 557  and sector_id in %(sector_ids)s"""
        else:
            consulta += """ where origen_id <> 557  and sector_id in %(sector_ids)s"""

    if self.sector_ids[0].id == 18:
        consulta += """ and origen_id in (520,522,524,521,523)"""

    if self.sector_ids[0].id == 19:
        consulta += """ and origen_id in (439,518,442,441,443,1021)"""

    consulta += """ GROUP BY sector,
                          categoria_interna;


                 """

    self.env.cr.execute(consulta,
                        {'ffecha_i': self.fecha_inicial + ' 00:00:00',
                         'ffecha_f': self.fecha_final + ' 23:59:59',
                         'sector_ids': tuple(self.sector_ids.ids),
                         'categoria_ids': tuple(self.categoria_ids.ids)

                         })

    resultado = self.env.cr.fetchall()
    totalCompra = 0
    totalFifo = 0
    for tupla in resultado:
        categoria = self.env['product.category'].search([('name', '=', tupla[0])])
        rubro_codigo_gastos_code = categoria.property_account_expense_categ.code
        rubro_codigo_gastos_name = categoria.property_account_expense_categ.name

        totalCompra += float(tupla[2])
        totalFifo += float(tupla[1])

        if (not categoria):
            # or rubro_codigo_gastos_code == '220000':
            rubro_codigo_gastos_code = '- SIN DEFINIR -'
            rubro_codigo_gastos_name = tupla[0]

        list_qweb.append(
            {
                'rubro': rubro_codigo_gastos_code,
                'categoria': rubro_codigo_gastos_name,
                'compra': tupla[2],
                'fifo': tupla[1],

            })

    list_qweb.append(
        {
            'rubro': ' ',
            'categoria': 'TOTAL DE BIENES',
            'compra': totalCompra,
            'fifo': totalFifo,

        })

    return list_qweb
