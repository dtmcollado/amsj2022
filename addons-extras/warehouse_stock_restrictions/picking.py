# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from openerp.exceptions import ValidationError
from openerp.osv import fields, osv
import datetime



class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def get_next_picking_for_ui(self, cr, uid, context=None):
        """ returns the next pickings to process. Used in the barcode scanner UI"""
        if context is None:
            context = {}
        domain = [('state', 'in', ('assigned', 'partially_available'))]
        if context.get('default_picking_type_id'):
            domain.append(('picking_type_id', '=', context['default_picking_type_id']))
        salida = self.search(cr, uid, domain, context=context)
        lista = []



        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        #
        # permite_transferir = False
        for picking_id in salida:
            for ubicacion in user.stock_location_stock_ids:
                # pick_obj = self.search(cr, uid, [('id', '=', picking_id)], context=context)
                pick_obj = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
                if ubicacion.id == pick_obj.location_id.id:
                    lista.append(pick_obj.id)
        # [958723, 947414, 944252, 941501, 941376, 933982, 918932, 898964, 828117]
        return lista