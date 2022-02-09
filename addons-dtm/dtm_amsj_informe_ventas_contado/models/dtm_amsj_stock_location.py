# -*- coding: utf-8 -*-
# from datetime import date, timedelta, time, datetime


from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import logging
import codecs
import base64
from datetime import datetime, timedelta
import time
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class dtm_amsj_stock_location_id_ubicacion(models.Model):
    _inherit = "stock.location"

    ventas_contado = fields.Boolean('Ventas Contado',defualt=False,copy=False)

dtm_amsj_stock_location_id_ubicacion()