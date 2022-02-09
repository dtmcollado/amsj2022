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
from openerp.osv import osv
from openerp.tools.translate import _
from openerp import api


class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def rereserve_pick(self, cr, uid, ids, context=None):
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.sector_id.id == 17:
                if picking.por_consumo or picking.por_extraordinario:
                    encontre = False
                    for linea in picking.move_lines:
                        if linea.state not in ('done', 'cancel'):
                            if not encontre:
                                cabezal = self.pool.get("dtm.amsj.consumos.cobol").create(cr, uid, {
                                    'name': picking.display_name,
                                    'almacen': 1
                                })
                            encontre = True
                            # u'assigned'  es OK
                            estado = linea.state
                            destino = linea.location_dest_id.id
                            tipo = linea.picking_type_id.id
                            origen = linea.location_id.id


                            self.pool.get("dtm.amsj.consumos.cobol.lineas").create(cr, uid, {
                                'name': linea.product_id.default_code,
                                'quantity': linea.product_qty,
                                'product_id': linea.product_id.id,
                                'importado_id': cabezal
                            })
                            if int(origen) == 551:
                                linea.write({'state': 'draft'})
                                linea.unlink()

                    if encontre:

                        cr.execute(
                            """
                                    SELECT * FROM 
                                    sp_reponer_cobol(%(importado_id)s,%(location_origen)s) 
                                    ;
    
                                """
                            , {
                                'importado_id': cabezal,
                                'location_origen': origen
                            }
                        )

                        resultado = cr.fetchall()

                        for tupla in resultado:
                            producto_id = tupla[0]
                            product_uom = tupla[2]
                            lote = tupla[3]
                            vencimiento = tupla[4]
                            cantidad_a_reponer = tupla[5]
                            disponible = tupla[6]

                            producto = self.pool.get('product.product').search(cr, uid, [
                                ('id', '=', producto_id),
                                ('tipo_de_empaque', '=', 1),],
                                                                context=context)

                            if cantidad_a_reponer > 0 and int(origen) == 551:
                                if disponible == 1:
                                    self.pool.get("stock.move").create(cr, uid, {
                                        'name': 'Por generico',
                                        'product_id': producto_id,
                                        'product_uom_qty': cantidad_a_reponer,
                                        'product_uom': product_uom,
                                        'picking_id': picking.id,
                                        'picking_type_id': tipo,
                                        'lote': lote,
                                        'state': 'assigned',
                                        'location_dest_id': destino,
                                        'location_id': origen,
                                    })
                                else:
                                    self.pool.get("stock.move").create(cr, uid, {
                                        'name': 'Sin Stock',
                                        'product_id': producto_id,
                                        'product_uom_qty': cantidad_a_reponer,
                                        'product_uom': product_uom,
                                        'picking_id': picking.id,
                                        'picking_type_id': tipo,
                                        'lote': lote,
                                        'location_dest_id': destino,
                                        'location_id': origen,
                                    })

        # for pick in self.browse(cr, uid, ids, context=context):
        #     self.rereserve_quants(cr, uid, pick, move_ids=[x.id for x in pick.move_lines
        #                                                    if x.state not in ('done', 'cancel')], context=context)

    # do_enter_transfer_details
    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        ubicaciones = user.stock_location_stock_ids or False

        if not ubicaciones:
            raise osv.except_osv(_('Aviso!'),
                                 _(
                                     u'Usuario no tiene definida ubicación con manejo de stock.' \
                                     '\nPor favor contacte al Administrador.'))

        for pick in self.browse(cr, uid, picking, context=context):
            permitido = False
            # if picking.location_id.usage in ('supplier', 'inventory', 'production'):
            for ubicacion in ubicaciones:
                if pick.location_id.id == ubicacion.id:
                    permitido = True

            if not permitido:
                raise osv.except_osv(_('Aviso!'),
                                     _(
                                         u'No puede mover stock de la ubicación' \
                                         '\nPor favor contacte al Administrador.'))

        if not context:
            context = {}
        else:
            context = context.copy()
        context.update({
            'active_model': self._name,
            'active_ids': picking,
            'active_id': len(picking) and picking[0] or False
        })

        created_id = self.pool['stock.transfer_details'].create(cr, uid,
                                                                {'picking_id': len(picking) and picking[0] or False},
                                                                context)
        return self.pool['stock.transfer_details'].wizard_view(cr, uid, created_id, context)

    def action_confirm(self, cr, uid, ids, context=None):

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        ubicaciones = user.stock_location_stock_ids or False

        if not ubicaciones:
            raise osv.except_osv(_('Aviso!'),
                                 _(
                                     u'Usuario no tiene definida ubicación con manejo de stock.' \
                                     '\nPor favor contacte al Administrador.'))

        for picking in self.browse(cr, uid, ids, context=context):
            permitido = False
            # if picking.location_id.usage in ('supplier', 'inventory', 'production'):
            for ubicacion in ubicaciones:
                if picking.location_id.id == ubicacion.id:
                    permitido = True

            if not permitido:
                raise osv.except_osv(_('Aviso!'),
                                     _(
                                         u'No puede mover stock de la ubicación' \
                                         '\nPor favor contacte al Administrador.'))

        super(stock_picking, self).action_confirm(cr, uid, ids, context=context)
        return True

    def action_assign(self, cr, uid, ids, context=None):

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        ubicaciones = user.stock_location_stock_ids or False

        if not ubicaciones:
            raise osv.except_osv(_('Aviso!'),
                                 _(
                                     u'Usuario no tiene definida ubicación con manejo de stock.' \
                                     '\nPor favor contacte al Administrador.'))

        for picking in self.browse(cr, uid, ids, context=context):
            permitido = False
            # if picking.location_id.usage in ('supplier', 'inventory', 'production'):
            for ubicacion in ubicaciones:
                if picking.location_id.id == ubicacion.id:
                    permitido = True

            if not permitido:
                raise osv.except_osv(_('Aviso!'),
                                     _(
                                         u'No puede mover stock de la ubicación' \
                                         '\nPor favor contacte al Administrador.'))
        # cesar 14/10/2020
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.sector_id.id == 17:
                if picking.por_consumo or picking.por_extraordinario:
                    encontre = False
                    for linea in picking.move_lines:
                        if linea.state not in ('done', 'cancel'):
                            if not encontre:
                                cabezal = self.pool.get("dtm.amsj.consumos.cobol").create(cr, uid, {
                                    'name': picking.display_name,
                                    'almacen': 1
                                })
                            encontre = True
                            # u'assigned'  es OK
                            estado = linea.state
                            destino = linea.location_dest_id.id
                            tipo = linea.picking_type_id.id
                            origen = linea.location_id.id

                            self.pool.get("dtm.amsj.consumos.cobol.lineas").create(cr, uid, {
                                'name': linea.product_id.default_code,
                                'quantity': linea.product_qty,
                                'product_id': linea.product_id.id,
                                'importado_id': cabezal
                            })
                            if int(origen) == 551:
                                linea.write({'state': 'draft'})
                                linea.unlink()

                    if encontre:

                        cr.execute(
                            """
                                    SELECT * FROM 
                                    sp_reponer_cobol(%(importado_id)s,%(location_origen)s) 
                                    ;

                                """
                            , {
                                'importado_id': cabezal,
                                'location_origen': origen
                            }
                        )

                        resultado = cr.fetchall()

                        for tupla in resultado:
                            producto_id = tupla[0]
                            product_uom = tupla[2]
                            lote = tupla[3]
                            vencimiento = tupla[4]
                            cantidad_a_reponer = tupla[5]
                            disponible = tupla[6]

                            producto = self.pool.get('product.product').search(cr, uid, [
                                ('id', '=', producto_id),
                                ('tipo_de_empaque', '=', 1), ],
                                                                               context=context)

                            if cantidad_a_reponer > 0 and int(origen) == 551:
                                if disponible == 1:
                                    self.pool.get("stock.move").create(cr, uid, {
                                        'name': 'Por generico',
                                        'product_id': producto_id,
                                        'product_uom_qty': cantidad_a_reponer,
                                        'product_uom': product_uom,
                                        'picking_id': picking.id,
                                        'picking_type_id': tipo,
                                        'lote': lote,
                                        'state': 'assigned',
                                        'location_dest_id': destino,
                                        'location_id': origen,
                                    })
                                else:
                                    self.pool.get("stock.move").create(cr, uid, {
                                        'name': 'Sin Stock',
                                        'product_id': producto_id,
                                        'product_uom_qty': cantidad_a_reponer,
                                        'product_uom': product_uom,
                                        'picking_id': picking.id,
                                        'picking_type_id': tipo,
                                        'lote': lote,
                                        'location_dest_id': destino,
                                        'location_id': origen,
                                    })
        #  fin cesar


        super(stock_picking, self).action_assign(cr, uid, ids, context=context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        ubicaciones = user.stock_location_stock_ids or False

        for record in self.browse(cr, uid, ids, context=context):

            if user.id != record.create_uid.id:

                if not ubicaciones:
                    raise osv.except_osv(_('Aviso!'),
                                         _(
                                             u'Usuario no tiene definida ubicación con manejo de stock.' \
                                             '\nPor favor contacte al Administrador.'))

                for picking in self.browse(cr, uid, ids, context=context):
                    permitido = False
                    # if picking.location_id.usage in ('supplier', 'inventory', 'production'):
                    for ubicacion in ubicaciones:
                        if picking.location_id.id == ubicacion.id:
                            permitido = True

                    if not permitido:
                        raise osv.except_osv(_('Aviso!'),
                                             _(
                                                 u'No puede mover stock de la ubicación' \
                                                 '\nPor favor contacte al Administrador.'))

            super(stock_picking, self).action_cancel(cr, uid, ids, context=context)
            return True

    # do_unreserve

    @api.cr_uid_ids_context
    def do_unreserve(self, cr, uid, picking_ids, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        ubicaciones = user.stock_location_stock_ids or False

        if not ubicaciones:
            raise osv.except_osv(_('Aviso!'),
                                 _(
                                     u'Usuario no tiene definida ubicación con manejo de stock.' \
                                     '\nPor favor contacte al Administrador.'))

        for picking in self.browse(cr, uid, picking_ids, context=context):
            permitido = False
            # if picking.location_id.usage in ('supplier', 'inventory', 'production'):
            for ubicacion in ubicaciones:
                if picking.location_id.id == ubicacion.id:
                    permitido = True

            if not permitido:
                raise osv.except_osv(_('Aviso!'),
                                     _(
                                         u'No puede mover stock de la ubicación' \
                                         '\nPor favor contacte al Administrador.'))

        # original
        moves_to_unreserve = []
        pack_line_to_unreserve = []
        for picking in self.browse(cr, uid, picking_ids, context=context):
            moves_to_unreserve += [m.id for m in picking.move_lines if m.state not in ('done', 'cancel')]
            pack_line_to_unreserve += [p.id for p in picking.pack_operation_ids]
        if moves_to_unreserve:
            if pack_line_to_unreserve:
                self.pool.get('stock.pack.operation').unlink(cr, uid, pack_line_to_unreserve, context=context)
            self.pool.get('stock.move').do_unreserve(cr, uid, moves_to_unreserve, context=context)

        # fin original

        cr.execute('''
            update stock_picking
            set state = 'draft'
            where id = %(stock_picking_id)s
        ''' % {'stock_picking_id': picking_ids[0]})

        ids2 = None
        for pick in self.browse(cr, uid, picking_ids, context=context):
            ids2 = [move.id for move in pick.move_lines]

        # self.pool.get('stock.move').action_cancel(cr, uid, ids2, context)
        # borrar del stock.move.reserved_quant_ids te dice el id de stock.quant, y de stock.quant borrar donde dice reservation_id
        quant_obj = self.pool.get("stock.quant")
        mov_obj = self.pool.get("stock.move")
        for mv in ids2:
            mov_obj_id = mov_obj.browse(cr, uid, mv, context=context)
            quant_obj.quants_unreserve(cr, uid, mov_obj_id, context=context)

            cr.execute('''
            update stock_move
            set state = 'draft'
            where id = %(stock_move_id)s
                ''' % {'stock_move_id': mv})


