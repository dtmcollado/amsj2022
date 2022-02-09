# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
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
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from datetime import date, datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools.float_utils import float_compare, float_round


class StockPicking(osv.Model):
    _inherit = 'stock.picking'

    def action_cancel_draft(self, cr, uid, ids, *args):
        uid = 1
        if not len(ids):
            return False
        move_obj = self.pool.get('stock.move')
        for (ids, name) in self.name_get(cr, uid, ids):
            message = _("Picking '%s' has been set in draft state.") % name
            self.message_post(cr, uid, ids, message)
        for pick in self.browse(cr, uid, ids):
            ids2 = [move.id for move in pick.move_lines]
            move_obj.action_draft(cr, uid, ids2)
        return True


class StockMove(osv.Model):
    _inherit = 'stock.move'
    
    
    def action_draft(self, cr, uid, ids, context=None):
        uid = 1
        res = self.write(cr, uid, ids, {'state': 'draft'}, context=context)
        return res
    
    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the moves and if all moves are cancelled it cancels the picking.
        @return: True
        """
        uid = 1
        procurement_obj = self.pool.get('procurement.order')
        context = context or {}
        procs_to_check = set()
        for move in self.browse(cr, uid, ids, context=context):
            ##manage quant
            if move.picking_id.state == 'done':
                
                pack_op = self.pool.get('stock.pack.operation').search(cr,uid,[('picking_id','=',move.picking_id.id),('product_id','=',move.product_id.id)])
                pack_op_browse = self.pool.get('stock.pack.operation').browse(cr,uid,pack_op[0])
                quant_ids = map(int, move.quant_ids)
                #outgoing
                if move.picking_id.picking_type_id.code in ['outgoing','internal']:
                    for move_id in quant_ids:
                        quants_ids = self.pool.get('stock.quant').browse(cr,uid,move_id)
                        for quant in quants_ids:
                            if pack_op_browse.location_dest_id.usage == 'customer':
                                self.pool.get('stock.quant').write(cr, uid, [move_id], {'location_id':move.location_id.id})
                            else:
                                if quant.lot_id:
                                    self.pool.get('stock.quant').write(cr, uid, [quant], {'location_id':move.location_id.id})
                #incoming
                if move.picking_id.picking_type_id.code == 'incoming':
                    for move_id in quant_ids:
                        quants_ids = self.pool.get('stock.quant').browse(cr,uid,move_id)
                        for quant in quants_ids:
                            if quant.lot_id:
                                quant.qty = 0.0
                            else:
                                quant.qty = 0.0
        res = self.write(cr, uid, ids, {'state': 'cancel', 'move_dest_id': False}, context=context)
        return res

        
