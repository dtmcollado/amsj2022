# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from datetime import date
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
import logging


class dtm_amsj_seguridad_productos(models.Model):
    _inherit = 'res.groups'
    sector = fields.Many2many(comodel_name='categoria', relation='categoria_group_rel', string='Sector')


class product_template(models.Model):
    _inherit = 'product.template'

    @api.multi
    @api.depends('current_user')
    def _compute_ocultar_botones(self):
        categoria = self[0].categoria_id.id
        usuario = False

        if categoria:
            grupos = self.env['res.groups'].search([('sector', '=', categoria)])
            list_group = [i.id for i in grupos]
            # usuario= self.env['res.groups.users.rel'].search([('uid','=',self._context['uid']),('gid','in',list_group)])
            if grupos:
                if self._context.get('uid'):
                    sql = '''select gid from res_groups_users_rel where uid = %(uid)s and gid in %(grupos)s  '''
                    self.env.cr.execute(sql, {'uid': self._context['uid'], 'grupos': tuple(list_group)})
                    usuario = self.env.cr.fetchall()
                    # print self.current_user,'User', self._context['uid']
                if usuario:
                    self[0].hide_action_buttons = False
                else:
                    self[0].hide_action_buttons = True
            else:
                self[0].hide_action_buttons = True
        else:
            self[0].hide_action_buttons = False

        if self._context.get('uid'):
            if self._context['uid'] == 1:
                self[0].hide_action_buttons = False

    @api.multi
    def _employee_get(self):
        if self.env.uid:
            return self.env.uid

        else:
            return self._context['uid']

    current_user = fields.Integer(string="Logged User", compute='_employee_get')
    hide_action_buttons = fields.Boolean('Esconde boton', compute='_compute_ocultar_botones')
