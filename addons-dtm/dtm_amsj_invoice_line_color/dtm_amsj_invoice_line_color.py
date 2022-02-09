
# -*- coding: utf_8 -*-
import ipdb as pdb
import math
import base64
from openerp import models, fields, api
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import Warning
from openerp.exceptions import ValidationError
from datetime import datetime



class dtm_amsj_invoice_line_color(models.Model):
    _inherit = 'account.invoice.line'
    color = fields.Boolean(string='Color', default=False)




class dtm_amsj_invoice(models.Model):
    _inherit = 'account.invoice'


