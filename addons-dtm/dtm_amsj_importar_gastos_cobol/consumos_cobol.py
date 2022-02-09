# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Datamatic All Rights Reserved.
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
from openerp.exceptions import Warning
from dateutil.relativedelta import relativedelta
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class dtm_amsj_compras_importadas(models.Model):
    _name = 'dtm.amsj.consumos.cobol'
    _order = "date desc, name desc, id desc"

    name = fields.Char(string=u'Referencia/Descripción', index=True)

    date = fields.Datetime(string='Fecha',
                           index=True, copy=False, default=datetime.now(), required=True)

    origin = fields.Char(string='Secuencia de importación', index=True)

    line_ids = fields.One2many('dtm.amsj.consumos.cobol.lineas',
                               'importado_id', string='Lineas CSV')

    almacen = fields.Many2one('aux.filiales', string='Filial')
    stock_picking_con_stock = fields.Many2one('stock.picking', string='Envio')
    stock_picking_sin_stock = fields.Many2one('stock.picking', string='Envio')

    state = fields.Selection([
        ('draft', 'Pendiente'),
        ('error', u'Código de Filial no es correcto'),
        ('done', u'Pedido Generado')
    ],
        string='Estado', index=True, readonly=True,
        default='draft', copy=False)

    #
    @api.multi
    def confirmar(self):
        filiales = self.env["aux.filiales"].browse()
        importado = self.id

        location_destino_id = self.almacen.almacen_id.in_type_id.default_location_dest_id.id

        location_origen = self.env['stock.location'].search(
            [
                ('codigo_amsj', '=', 'SJMFAR')
            ]
        )


        self.env.cr.execute(
            """
                    SELECT * FROM 
                    sp_reponer_cobol(%(importado_id)s,%(location_origen)s) 
                    where stock <> 4;

                """
            , {
                'importado_id': importado,
                'location_origen': location_origen.id
            }
        )

        resultado = self.env.cr.fetchall()
        primero = True
        picking_out = False

        for tupla in resultado:
            producto_id = tupla[0]
            product_uom = tupla[2]
            lote = tupla[3]
            vencimiento = tupla[4]
            cantidad_a_reponer = tupla[5]
            disponible = tupla[6]

            ubicacion_principal = self.env['stock.location'].search([
                ('almacen_id', '=', self.almacen.almacen_id.id),
                ('principal_del_expendio', '=', True)
            ])

            producto = self.env['product.product'].search([
                ('id', '=', producto_id),
                ('tipo_de_empaque', '=', 1),
            ])

            # DU
            # ('tipo_de_empaque', '=', 2),
            # ('presentacion_id', '=', 125)]

            if ubicacion_principal:
                ubicacion_principal = ubicacion_principal[0]

            if primero:

                picking_out = self.env['stock.picking'].create({
                    'location_dest_id': location_destino_id,
                    'location_id': location_origen.id,
                    'por_consumo_cobol': True,
                    'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                    'origin': 'Reposición por consumo especial '
                })

                if cantidad_a_reponer > 0:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out.id,
                        'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': location_destino_id,
                        'location_id': location_origen.id,

                    })

                primero = False

            else:
                try:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out.id,
                        'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': location_destino_id,
                        'location_id': location_origen.id,
                    })
                except Exception as e:
                    continue

        # *****************

        # *****  pedido sin stock *******
        self.env.cr.execute(
            """
                        SELECT * FROM  sp_reponer_cobol(%(importado_id)s,%(location_origen)s) 
                        where stock = 6;

                    """
            , {
                'importado_id': importado,
                'location_origen': location_origen.id
            }
        )

        resultado = self.env.cr.fetchall()
        primero_2 = True
        picking_out2 = False

        for tupla in resultado:
            producto_id = tupla[0]
            product_uom = tupla[2]
            lote = tupla[3]
            vencimiento = tupla[4]
            cantidad_a_reponer = tupla[5]
            disponible = tupla[6]

            if primero_2:

                if cantidad_a_reponer > 0:
                    picking_out2 = self.env['stock.picking'].create({
                        'location_dest_id': location_destino_id,
                        'location_id': location_origen.id,
                        'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                        'por_consumo_cobol': True,
                        'origin': 'Reposición por consumos especial',
                        'note': 'SIN STOCK a la fecha de armar pedido'
                    })

                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo especial',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out2.id,
                        'lote': lote,
                        'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                        'location_dest_id': location_destino_id,
                        'location_id': location_origen.id,
                    })
                    # actualizo fecha ultima reposicion

                    primero_2 = False

            else:
                if cantidad_a_reponer > 0:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo SIN STOCK',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out2.id,
                        'picking_type_id': self.almacen.almacen_id.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': location_destino_id,
                        'location_id': location_origen.id
                    })

        if primero and primero_2:

            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    'title': 'Pedidos',
                    'text': 'No se encontraron productos para generar pedido',
                    'sticky': True
                }
            }
        else:

            # if picking_out2:
            #     if picking_out2.state == 'draft':
            #         picking_out2.action_confirm()
            #         picking_out2.action_assign()

            if picking_out:

                # *******
                # if picking_out.state == 'draft':
                #     picking_out.action_confirm()
                #     picking_out.action_assign()
                dominio = picking_out.id
            # else:
            #
            #     dominio = picking_out2.id

            # *****
            # pendientes = self.env['stock.picking'].search([
            #     ('picking_type_id', '=', self.almacen.almacen_id.int_type_id.id),
            #     ('state', '!=', 'done'),
            #     ('state', '!=', 'cancel'),
            #     ('id','!=',picking_out.id ),
            #     ('id','!=',picking_out2.id),
            #     ('por_consumo_cobol', '=', True),
            #     ('location_id', '=', location_origen.id),
            #     ('location_dest_id', '=', location_destino_id)
            #
            # ], limit=None)
            #
            # for pendiente in pendientes:
            #     if (not pendiente.id == picking_out.id) or (not pendiente.id == picking_out2.id):
            #         for linea in pendiente.move_lines:
            #             if linea.state != 'done':
            #                 xproduct_id = linea.product_id.id
            #                 xproduct_uom_qty = linea.product_uom_qty
            #                 xproduct_uom = linea.product_uom.id
            #
            #                 if xproduct_uom_qty > 0:
            #                     self.env['stock.move'].create({
            #                         'name': 'Reposición de ' + str(pendiente.name),
            #                         'product_id': xproduct_id,
            #                         'product_uom_qty': xproduct_uom_qty,
            #                         'product_uom': xproduct_uom,
            #                         'picking_id': dominio,
            #                         'picking_type_id': self.almacen.almacen_id.int_type_id.id,
            #                         'lote': False,
            #                         'location_dest_id': location_destino_id,
            #                         'location_id': location_origen.id,
            #                     })
            #
            #                 cr = self.env.cr
            #                 uid = self.env.uid
            #                 context = self.env.context.copy()
            #
            #                 self.pool.get('stock.move').action_cancel(cr, uid, linea.id, context)
            #
            #         self.pool.get('stock.picking').action_cancel(cr, uid, pendiente.id, context)

            if picking_out:
                self.write({'stock_picking_con_stock': picking_out.id})
            # if picking_out2:
            #     self.write({'stock_picking_sin_stock': picking_out2.id})

            self.write({'state': 'done'})
            return {
                'domain': [('id', '=', dominio)],
                'name': 'x Consumo especial',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.picking.tree'},
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window'}


class dtm_amsj_compras_importadas_lineas(models.Model):
    _name = 'dtm.amsj.consumos.cobol.lineas'

    name = fields.Text(string='Description', required=True)
    importado_id = fields.Many2one('dtm.amsj.consumos.cobol', string='Referencia Compra Importada',
                                   ondelete='cascade', index=True)

    producto = fields.Integer(string='Producto')
    product_id = fields.Many2one('product.product', string='Producto',
                                 ondelete='restrict', index=True)
    quantity = fields.Integer(string='Cantidad', required=True, default=1)

    almacen = fields.Integer(string='Almacen')
    # almacen

    state = fields.Selection([
        ('done', 'Validada'),
        ('error1', u'Tipo de empaque mal'),
        ('error2', u'Error'),
    ],
        string='Estado', index=True, readonly=True,
        default='done', copy=False)
