# -*- coding: utf-8 -*-
# from datetime import date, timedelta, time, datetime


import logging

from openerp import models

_logger = logging.getLogger(__name__)
LOCATION_ID = 551
CATEGORIA_FARMACIA = 17


class dtm_amsj_pasaje_a_vendido(models.Model):
    _inherit = 'stock.picking'

    def cron_pasaje_a_cancelado(self, cr, uid, context=None):

        sql = """
                UPDATE stock_picking 
                SET state = 'cancel' , note = 'Cancelado por proceso automatico mas de 30 dias'
                WHERE betweenDays(dATE(create_date)) > 30 AND origin like 'PO%' and state = 'assigned' and sector_id = 17;
            """
        cr.execute(sql)


