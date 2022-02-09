# -*- coding: utf_8 -*-
from openerp import models, fields, _, api, exceptions
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import locale
import time
import logging
import ipdb as pdb
from openerp.exceptions import Warning
_logger = logging.getLogger(__name__)

class dtm_actualizacion_stock(models.Model):

    _inherit='product.template'
    #_name = 'dtm.actualizacion.stock'
  