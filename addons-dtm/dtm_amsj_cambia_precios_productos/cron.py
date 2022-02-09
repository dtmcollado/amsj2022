# -*- coding: utf-8 -*-
from openerp import models, fields, api
# Import logger
import logging
import time
from datetime import date
from datetime import timedelta

# Get the logger
_logger = logging.getLogger(__name__)

# External import
import datetime


class scheduler_precio_costo(models.Model):
    _name = 'scheduler.precio.costo'

    name = fields.Char(string='Nombre', readonly=True)
    ejecuto_bien = fields.Boolean(string='Se actualizo', readonly=True)
    fecha = fields.Date(string='Fecha', readonly=True)

    def process_amsj_scheduler_queue(self, cr, uid, context=None):
        scheduler_line_obj = self.pool.get('scheduler.precio.costo')

        scheduler_line_ids = self.pool.get('scheduler.precio.costo').search(cr, uid, [])

        for scheduler_line_id in scheduler_line_ids:
            scheduler_line = scheduler_line_obj.browse(cr, uid, scheduler_line_id, context=context)
            # numberOfUpdates = scheduler_line.numberOfUpdates
            _logger.info('line: ' + scheduler_line.name)
            # scheduler_line_obj.write(cr, uid, scheduler_line_id, {'numberOfUpdates': (numberOfUpdates + 1),
            #                                                       'lastModified': datetime.date.today()},
            #                          context=context)

    @api.multi
    def process_amsj_scheduler_test(self):
        vals = {}
        vals['fecha'] = date.today()
        vals['name'] = "Ejecuto scheduler_test"
        vals['ejecuto_bien'] = True
        self.create(vals)
        return
