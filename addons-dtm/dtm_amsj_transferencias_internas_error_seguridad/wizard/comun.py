# -*- coding: utf-8 -*-
from datetime import date

from openerp import models, fields, api, exceptions
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning
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
                'picking_type_id': wharehouse.int_type_id.id,
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
                'picking_type_id': wharehouse.int_type_id.id,
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

    @api.multi
    def validar_productos_del_pedido(self):
        for record in self:
            productos_invalidos = str()
            sector_seleccionado = record.expendios_location_orig_id.sector

            for linea_de_productos in record.move_lines:
                producto = linea_de_productos.product_id
                categoria_del_producto = producto.categoria_id

                if categoria_del_producto.id != sector_seleccionado.id:
                    productos_invalidos += '[%(codigo)s] %(nombre)s\n' % {'codigo': producto.code,
                                                                          'nombre': producto.name}

            if productos_invalidos:
                raise ValidationError(
                    "Los siguientes Productos NO pertenecen al Sector %(sector)s:\n\n%(productos)s" % {
                        'sector': sector_seleccionado.name,
                        'productos': productos_invalidos,
                    })

    @api.multi
    def action_create_reposicion(self):
        self.validar_productos_del_pedido()

        # try:
        user = self.env["res.users"].browse([self.env.uid])
        location_ids = [loc.id for loc in user.stock_location_ids]
        wharehouses = self.env['stock.warehouse'].search([
            ('wh_output_stock_loc_id', 'in', location_ids)
        ])

        if len(wharehouses) == 1:
            wharehouse = wharehouses[0]
        else:
            wharehouses = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', '=', self.expendios_location_dest_id.id)
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

        ubicacion_principal = self.env['stock.location'].search([
            ('almacen_id', '=', wharehouse.id),
            ('principal_del_expendio', '=', True)
        ])

        if ubicacion_principal:
            ubicacion_principal = ubicacion_principal[0]

        origen = self.expendios_location_orig_id

        destino_id = self.expendios_location_dest_id

        picking_out = self.env['stock.picking'].create({
            "location_id": origen,
            'location_dest_id': destino_id.id,
            'picking_type_id': wharehouse.int_type_id.id,
            'note': '>>> Reposición extraordinaria <<<'
        })

        # picking_out.message_post(body='Albarán creado')

        for line in self.move_lines:
            cant = line.product_qty

            if ubicacion_principal.stock_critico:
                for stock_maximo in ubicacion_principal.stock_critico:
                    if stock_maximo.product_tmpl_id.id == line.product_id.product_tmpl_id.id:
                        maximo = stock_maximo.stock_critico

                        # stock actual
                        quants = self.env['stock.quant'].search([('location_id', 'child_of', ubicacion_principal.id),
                                                                 ('product_id.product_tmpl_id', '=',
                                                                  line.product_id.product_tmpl_id.id),
                                                                 ('reservation_id', '=', None),
                                                                 ])
                        stock_actual = sum(quants.mapped('qty'))

                        if stock_actual < maximo:
                            cant = maximo - stock_actual
                            Warning(
                                u"Cantidad supera stock maximo: " + line.product_id.name + "cantidad se cambia a " + cant)
                        else:
                            cant = 0

                        if line.product_qty < cant:
                            cant = line.product_qty

            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': cant,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_out.id,
                'picking_type_id': wharehouse.int_type_id.id,
                'location_id': self.expendios_location_orig_id.id,
                'location_dest_id': destino_id.id,
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
    # except Exception:
    #     raise exceptions.Warning(_("Almacen o Ubicacion MAL configurado. Contacte Administrador"))


wizard()
