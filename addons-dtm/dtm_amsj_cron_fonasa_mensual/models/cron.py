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
import datetime


class scheduler_demo(models.Model):
    _name = 'scheduler.fonasa'
    name = fields.Char(required=True)
    numberOfUpdates = fields.Integer('Number of updates', help='The number of times the scheduler has run and updated this field')
    lastModified = fields.Date('Last updated')

    def process_fonasa_scheduler_queue(self, cr, uid, context=None):
        cr.execute('DROP TABLE IF EXISTS consumos_BI;')

        sql = """
        create table consumos_BI as
                            select   fecha as Fecha,
                          CodMSP,product_template_name,product_qty,
              ValorFIFOUnitario as FIFO_Unitario,
			  total_fifo as FIFO_Total,
	  		  ValorUltCompraUnit as PUC_Unitario,

              total_ultima_compra as PUC_Total ,
			  destino as UbicacionDestino,SUBSTRING(destino,6,30) as tipo , transaccion_id as id_transaccion
                FROM

              sp_consumos_mov_report_BI('2020-07-25 00:00:00',
        """
        # '2021-07-31 23:59:59'\
        ultimoDiaMesAnterior = datetime.date.today().replace(day=1) + datetime.timedelta(days=-1)
        fecha = "'" + str(ultimoDiaMesAnterior) + " 23:59:59'"
        sql += fecha
        sql += """,'17',1,'','','') ; """

        cr.execute(sql)
