# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.odoo.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import ipdb as pdb
#import math
#import base64
#import datetime
#import cPickle as pickle

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError

class esperando_disponibilidad(models.Model):

    _inherit = 'stock.picking'

    # @api.multi
    # def write(self, vals):
    #     if 'backorder_id' in vals and vals['backorder_id'] != False:
    #         self._cr.execute('UPDATE STOCK_PICKING SET CREATE_DATE = %s WHERE ID=%s',(self.create_date,vals['backorder_id']))
    #     return super(esperando_disponibilidad, self).write(vals)

esperando_disponibilidad()

