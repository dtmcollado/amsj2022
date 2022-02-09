# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Datamatic All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from datetime import datetime, date, timedelta

import os
import base64

import xlwt
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO
from openerp import tools


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    # _order = "id desc"



    # ---    SE COMENTA PORQUE DA PROBLEMAS DE PERFORMACE ------  CESAR 07/05/20   ------------
    #
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #
    #     admin = self.env.user.has_group('base.group_system')
    #
    #     if not admin:
    #
    #         ids_stock = []
    #
    #         user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
    #
    #         for location_stock in user.stock_location_ids:
    #             ids_stock.append(location_stock.id)
    #
    #         location_ids_stock = ids_stock[:]
    #
    #         args.append(('location_id.id', 'in', (location_ids_stock)))
    #         args.append(('location_dest_id.id', 'in', (location_ids_stock)))
    #
    #     return super(StockPicking, self).search(args, offset, limit, order, count=count)
