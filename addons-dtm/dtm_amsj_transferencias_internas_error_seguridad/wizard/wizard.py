# -*- coding: utf-8 -*-
from datetime import date

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

CREATE = lambda values: (0, False, values)
UPDATE = lambda id, values: (1, id, values)
DELETE = lambda id: (2, id, False)
FORGET = lambda id: (3, id, False)
LINK_TO = lambda id: (4, id, False)
DELETE_ALL = lambda: (5, False, False)
REPLACE_WITH = lambda ids: (6, False, ids)


class wizline(models.TransientModel):
    _name = "wizard.transferencia.interna.line"

    @api.multi
    @api.depends('product_uom_qty')
    def _quantity_normalize(self):
        for each in self:
            each.product_qty = each.product_uom_qty

    generico_id = fields.Many2one('principio.activo', 'Genérico')
    product_id = fields.Many2one('product.product', 'Product',
                                 required=True, select=True)

    # domain=[('type', '<>', 'service')])
    product_qty = fields.Float('Quantity', compute='_quantity_normalize',
                               help='Quantity in the default UoM of the product')
    product_uom_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                   required=True,
                                   help="This is the quantity of products from an inventory "
                                        "point of view. For moves in the state 'done', this is the "
                                        "quantity of products that were actually moved. For other "
                                        "moves, this is the quantity of product that is planned to "
                                        "be moved. Lowering this quantity does not generate a "
                                        "backorder. Changing this quantity on assigned moves affects "
                                        "the product reservation, and should be done with care."
                                   )
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True,
                                  readonly=True, related=('product_id', 'uom_id'))
    transf_id = fields.Many2one('wizard.transferencia.interna')


class wizard(models.TransientModel):
    _name = "wizard.transferencia.interna"


    location_dest_readonly = fields.Boolean()

    move_lines = fields.One2many('wizard.transferencia.interna.line', inverse_name='transf_id', String='Internal Moves',
                                 copy=True)

    # @api.one
    # @api.constrains('new_location_dest_id')
    # def check_user_location_rights(self):
    #     user_locations = self.env.user.stock_location_ids
    #     if self.env.user.restrict_locations and \
    #                     self.new_location_dest_id not in user_locations:
    #
    #         name = self.new_location_dest_id.name
    #         if type(name) == unicode:
    #             name = name.encode("utf-8")
    #
    #         message = (
    #                       'Ubicación inválida. No puede procesar este movimiento  '
    #                       'no tiene permisos en "%s". '
    #                       'Contacte al Administrador.') % name
    #
    #         raise Warning(message)



    # @api.multi
    # def action_refrescar(self):
    #     #       busco si tiene lista.
    #     lineas = self.env["wizard.transferencia.interna.line"]
    #
    #     for item in self.new_location_dest_id.lista_productos_ids:
    #         if item.sourceloc_id.id == self.new_location_orig_id.id:
    #             # agrego a move_lines  [(6,0,liqs)]
    #             # self.move_lines.write({'product_id': [(4, item.product_id.id)]})
    #             lineas.create(
    #                 {
    #                     'product_id': item.product_id.id,
    #                     'product_uom': item.product_id.uom_id.id,
    #                     'product_qty': 0,
    #                     'generico_id': False,
    #                     'product_uom_qty': 0,
    #                     'transf_id': self.id
    #                 }
    #             )
    #
    #     self.write({'move_lines': [(4, x) for x in lineas]})
    #
    #     self.ensure_one()
    #
    #     return {
    #         'context': self.env.context,
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'wizard.transferencia.interna',
    #         'res_id': self.id,
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #     }




    @api.multi
    def action_create_transferencia_interna(self):

        # wharehouses = self.env['stock.warehouse'].search([
        #     ('wh_input_stock_loc_id', '=', self.internal_location_dest_id.id)
        # ])

        user = self.env["res.users"].browse([self.env.uid])
        location_ids = [loc.id for loc in user.stock_location_ids]
        wharehouses = self.env['stock.warehouse'].search([
            ('wh_output_stock_loc_id', 'in', location_ids)
        ])

        if len(wharehouses) > 0:
            wharehouse = wharehouses[0]
        else:
            wharehouses = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', 'in', location_ids)
            ])
            if len(wharehouses) > 0:
                wharehouse = wharehouses[0]

        if self.internal_location_dest_id.id == self.internal_location_orig_id.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": "Origen y Destino deben de ser diferentes",
                    "sticky": True,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": self.internal_location_orig_id,
            'location_dest_id': self.internal_location_dest_id.id,
            'picking_type_id': wharehouse.int_type_id.id,
        })

        # picking_out.message_post(body='Albarán creado')

        for line in self.move_lines:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_out.id,
                'location_id': self.internal_location_orig_id.id,
                'location_dest_id': self.internal_location_dest_id.id,
                'state': "confirmed",
            })

        if len(self.move_lines) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia Interna",
                    "text": "No se encontraron productos para generar transferencia",
                    "sticky": True,
                }
            }

    @api.multi
    def action_create_transferencia_expendio(self):

        # wharehouses = self.env['stock.warehouse'].search([
        #     ('wh_input_stock_loc_id', '=', self.internal_location_dest_id.id)
        # ])

        user = self.env["res.users"].browse([self.env.uid])
        location_ids = [loc.id for loc in user.stock_location_ids]
        wharehouses = self.env['stock.warehouse'].search([
            ('wh_output_stock_loc_id', 'in', location_ids)
        ])

        if len(wharehouses) > 0:
            wharehouse = wharehouses[0]
        else:
            wharehouses = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', 'in', location_ids)
            ])
            if len(wharehouses) > 0:
                wharehouse = wharehouses[0]



        if self.expendios_location_dest_id.id == self.expendios_location_orig_id.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": "Origen y Destino deben de ser diferentes",
                    "sticky": True,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": self.expendios_location_orig_id,
            'location_dest_id': self.expendios_location_dest_id.id,
            'picking_type_id': wharehouse.int_type_id.id,
        })

        # picking_out.message_post(body='Albarán creado')

        for line in self.move_lines:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_out.id,
                'location_id': self.expendios_location_orig_id.id,
                'location_dest_id': self.expendios_location_dest_id.id,
                'state': "confirmed",
            })

        if len(self.move_lines) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": "No se encontraron productos para generar transferencia",
                    "sticky": True,
                }
            }

    def stock_disponible(self, producto_id):
        #  verifico stock disponible
        quants = self.env['stock.quant'].search(
            [('location_id', 'child_of', self.origen.id), ('product_id', '=', producto_id),
             ('reservation_id', '=', False)])
        cantidad_disponible = sum(quants.mapped('qty'))
        return cantidad_disponible


wizard()
