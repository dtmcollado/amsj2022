# -*- coding: utf_8 -*-
import ipdb as pdb
import math
import base64
from openerp import models, fields, api
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import Warning
from openerp.exceptions import ValidationError
from datetime import datetime


class dtm_amsj_devolucion_productos(models.Model):
    _inherit = 'stock.transfer_details'

    @api.multi
    def do_detailed_transfer(self):

        result = super(dtm_amsj_devolucion_productos, self).do_detailed_transfer()
        supplier = False

        var_moves = []
        if self.item_ids:

            for i in self.item_ids:
                if i.destinationloc_id.usage == 'supplier':
                    supplier = True
                    var_m = {'product_id': i.product_id.id,
                             'quantity': i.quantity
                             }
                    var_moves.append(var_m)

            if supplier:
                pi = self.picking_id

                if pi:
                    get_picking = {
                        'company_id': pi.company_id.id if pi.company_id else None,
                        'date': datetime.now(),

                        'distribuido': True,
                        'group_id': pi.group_id.id if pi.group_id else None,

                        'invoice_state': pi.invoice_state if pi.invoice_state else None,
                        'location_dest_id': pi.location_dest_id.id if pi.location_dest_id else None,
                        'location_id': pi.location_id.id if pi.location_id else None,

                        'move_type': pi.move_type,

                        'origin': [i.origin for i in pi.move_lines][0] if pi.move_lines else None,
                        'owner_id': pi.owner_id.id if pi.owner_id else None,

                        'partner_id': pi.partner_id.id if pi.partner_id else None,
                        'picking_type_code': 'incoming',

                        'picking_type_id': pi.picking_type_id.id if pi.picking_type_id else None,
                        'priority': pi.priority,

                        'sector_id': pi.sector_id.id,
                        'state': 'assigned',

                    }

                    if len(var_moves) > 0:
                        picking_new = self.env['stock.picking'].create(get_picking)
                        #
                        picking_new.write(
                            {'picking_type_id': 151, 'picking_type_code': 'incoming'})
                        # picking_type_id = 151
                        origin = picking_new.origin
                        purchase_order = self.env['purchase.order'].search([('name', '=', origin)])

                    for line in var_moves:
                        line_moves = self.env['stock.move'].search(
                            [('picking_id', '=', pi.id), ('product_id', '=', line['product_id'])])
                        purchase_order_line = self.env['purchase.order.line'].search(
                            [('order_id', '=', purchase_order.id), ('product_id', '=', line['product_id'])])
                        if len(line_moves) > 1:
                            line_moves = line_moves[0]
                        nuevo = self.env['stock.move'].create({
                            'name': line_moves.product_id.name,
                            'product_id': line_moves.product_id.id,
                            'product_uom_qty': line['quantity'],
                            'product_uom': line_moves.product_uom.id,
                            'picking_id': picking_new.id,
                            'picking_type_id': 151,
                            'location_id': line_moves.location_dest_id.id,
                            'location_dest_id': line_moves.location_id.id,
                            'origin': picking_new.origin,
                            'purchase_line_id': purchase_order_line[0].id if purchase_order_line[0] else None,
                            'state': "assigned",
                            'lot_id': line_moves.lot_ids.id if line_moves.lot_ids else None,
                            'date': datetime.now(),
                        })

                return {
                    'domain': "[('id', 'in', [" + str(purchase_order.id) + "])]",
                    'name': 'Devolución Albarán',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'purchase.order',
                    'type': 'ir.actions.act_window',
                }


class stock_return_farmacia(models.Model):
    _inherit = 'stock.return.picking'
    _description = 'Return Picking Farmacia'

    # Pedro - para las devoluciones que van a farmacia de AMSJ las envio a Recepcion
    @api.multi
    def _create_returns(self):
        new_picking, picking_type_id = super(stock_return_farmacia, self)._create_returns()
        if new_picking:
            pick_new = self.env['stock.picking'].search([('id', '=', new_picking)])
            if pick_new.location_dest_id.id == 551:
                pick_new.location_dest_id = 552
                pick_new.distribuido = False
                movs = self.env['stock.move'].search([('picking_id', '=', new_picking)])
                for m in movs:
                    m.sudo().write({'location_dest_id': 552, 'distribuido': False})
        return new_picking, picking_type_id
