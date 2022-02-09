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


class dtm_facturas_con_diferencia(models.Model):
    _inherit = 'facturas.diferencia.entrega'

    @api.multi
    def factura_wizard(self):
        self.ensure_one()
        # form_id = self.env.ref('dtm_mtop_compras.view_purchase_order_form_wizard_create_auto')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': form_id.id,
            'view_id': False,
            'res_model': 'account.invoice',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def remito_wizard(self):
        self.ensure_one()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': form_id.id,
            'view_id': False,
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }


dtm_facturas_con_diferencia()
