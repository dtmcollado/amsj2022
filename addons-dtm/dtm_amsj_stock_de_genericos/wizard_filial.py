# -*- coding: utf-8 -*-

from datetime import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
import os
import base64

import xlwt
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

import datetime, time
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO


class wizard_minimo_amsj(models.TransientModel):
    _name = 'wizard.filial.maximo'

    @api.multi
    def get_domain(self):

        user = self.env['res.users'].browse([self.env.user.id])
        con_sector = []

        for location in user.stock_location_stock_ids:

            if not location.scrap_location:
                if location.stock_critico:
                    con_sector.append(location.id)

        location_ids = con_sector[:]  # list.copy se agregó en python 3.3
        # location.stock_critico_ids
        return [('id', '=', location_ids)]

    location_id = fields.Many2one('stock.location', 'Ubicacion', required=True, domain=get_domain)
    sector_id = fields.Many2one(string=u'Sector', comodel_name='categoria', required=True)


    @api.multi
    def open_table(self):
        self.ensure_one()
        view = self.env.ref('dtm_amsj_stock_de_genericos.ubicacion_filial_tree_view')
        ctx = self.env.context.copy()
        ctx.update({'ubicacion': self.location_id.id})

        if self.sector_id.id == 17:
            view = self.env.ref('dtm_amsj_stock_de_genericos.ubicacion_stock_filial_tree_view')

            return {
                'name': _('Stock Maximo') + ": %s" % (self.location_id.complete_name),
                'view_type': 'form',
                'view_mode': 'tree',
                'domain': [('ubicacion_id', '=', self.location_id.id)],
                'view_id': view.id,
                'res_model': 'dtm.amsj.stock.de.genericos',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'flags': {'search_view': True, 'action_buttons': True},
                'ubicacion': self.location_id.id,
                'context': ctx,
            }


        else:
            return {
                'name': _('Stock Maximo') + ": %s" % (self.location_id.complete_name),
                'view_type': 'form',
                'view_mode': 'tree',
                'domain': [('ubicacion_id', '=', self.location_id.id),('sector_id', '=', self.sector_id.id)],
                'view_id': view.id,
                'res_model': 'dtm.amsj.stock.maximo.filial',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'flags': {'search_view': True, 'action_buttons': True},
                'ubicacion': self.location_id.id,
                'context': ctx,
            }


