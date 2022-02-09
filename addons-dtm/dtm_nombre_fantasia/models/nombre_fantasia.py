# -*- coding: utf_8 -*-
from openerp import models, fields, _, api, exceptions
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
import locale
import time
import logging
import ipdb as pdb
from openerp.exceptions import Warning
_logger = logging.getLogger(__name__)

class res_partner(models.Model):

    _inherit='res.partner'

    fantasia = fields.Char(string="Nombre Fantasia", size=128)

res_partner()

class res_company(models.Model):

    _inherit='res.company'

    fantasia = fields.Char(string="Nombre Fantasia", size=128)

res_company()
