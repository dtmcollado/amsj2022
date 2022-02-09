# -*- coding: utf-8 -*-
# from datetime import date, timedelta, time, datetime


from openerp import models, fields, SUPERUSER_ID, exceptions, api, _
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import logging
import codecs
import base64
from datetime import datetime, timedelta
import time
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)
LOCATION_ID = 551
CATEGORIA_FARMACIA = 17


class dtm_amsj_stock_warehouse(models.Model):
    _inherit = "stock.warehouse"

    emails_vencidos = fields.Char('Emails vencidos')


class dtm_amsj_stock_quant(models.Model):
    _inherit = "stock.quant"

    sent = fields.Boolean('Enviado')


class dtm_amsj_stock_location_id_ubicacion(models.Model):
    _inherit = "stock.location"

    laboratorio_id = fields.Many2one('res.partner', string='Laboratorio', copy=False)
    # dias_antes_vencimiento = fields.Integer(u'Días antes del vencimiento')


dtm_amsj_stock_location_id_ubicacion()


class dtm_amsj_pasaje_a_vendido(models.Model):
    _inherit = 'stock.picking'

    def cron_pasaje_a_vencido(self, cr, uid, context=None):
        quants = []
        fecha_hoy = datetime.today()
        locations = []
        warehouse_ids= self.pool.get('stock.warehouse').search(cr, uid,[('emails_vencidos', '!=', False)])
        for warehouse in self.pool.get('stock.warehouse').browse(cr,uid,warehouse_ids):
            location_ids = self.pool.get('stock.location').search(cr, uid,[('almacen_id', '=', warehouse.id)])
            sql = """
                SELECT quant.id 
                FROM stock_quant quant, stock_location location, 
                product_supplierinfo product_supplier, product_product product, 
                product_template product_tmpl, stock_production_lot lot
                WHERE 
                   quant.product_id = product.id and
                   product_tmpl.id = product.product_tmpl_id and
                   quant.lot_id = lot.id and 
                   product_supplier.name = location.laboratorio_id and
                   product_tmpl.id = product_supplier.product_tmpl_id and
                   lot.product_id = product.id and
                   location.laboratorio_id is not null and
                   quant.lot_id is not null and quant.qty > 0 and lot.alert_date <= %s 
                   and location.id IN %s and quant.location_id = location.id 
                   and (quant.sent = False or quant.sent isnull)
                   and reservation_id IS NULL
                """
            cr.execute(sql, (fecha_hoy,tuple(location_ids),))
            resultado = cr.fetchall()
            for res in resultado:
                    quant_id = res[0]
                    quants.append(quant_id)
                    self.pool.get('stock.quant').write(cr, uid, [quant_id], {'sent': 'True'})
            if quants:
                users_to_send = warehouse.emails_vencidos
                odoobot = "odoo@amsj.com.uy"
                message_body = '<br/>'
                message_body += 'Listado de transferencia automatica de productos por vencer o vencidos:'
                message_body += '<br/>'
                for quant in self.pool.get('stock.quant').browse(cr, uid, quants):
                    fecha_ven = str(quant.fecha_ven) or 'No ingresada'
                    fecha_alerta = quant.lot_id.alert_date or 'No ingresada'
                    message_body += '<br/>'
                    message_body += '<b>Nombre producto: </b>' + quant.product_id.name + ' <b>Cantidad: </b>' + str(
                        quant.qty) + ' <b>Fecha vencimiento: </b>' + fecha_ven + ' <b>Fecha de alerta: </b>' + fecha_alerta + ' <b>Lote: </b>' + quant.lot_id.name
                    message_body += '<br/>'
                mail = self.pool.get('mail.mail')
                today = datetime.now().strftime('%d/%m/%Y')
                mail_data = {
                    'subject': 'Listado de transferencia automatica de productos por vencer o vencidos ' + str(today),
                    'email_from': odoobot,
                    'email_to': users_to_send,
                    'body_html': message_body}
                mail_out = mail.create(cr, SUPERUSER_ID, mail_data)
                if mail_out:
                    mail.send(cr, SUPERUSER_ID, [mail_out])

