# -*- coding: utf-8 -*-
from datetime import date

from openerp import models, fields, api
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp

CREATE = lambda values: (0, False, values)
UPDATE = lambda id, values: (1, id, values)
DELETE = lambda id: (2, id, False)
FORGET = lambda id: (3, id, False)
LINK_TO = lambda id: (4, id, False)
DELETE_ALL = lambda: (5, False, False)
REPLACE_WITH = lambda ids: (6, False, ids)


class wizline(models.TransientModel):
    _name = "wizard.reg.consumos.line"

    @api.multi
    @api.depends('product_uom_qty')
    def _quantity_normalize(self):
        for each in self:
            each.product_qty = each.product_uom_qty

    product_id = fields.Many2one('product.product', 'Product',
                                 required=True, select=True)

    stock = fields.Float('Cantidad Actual', store=True)
    stock_bak = fields.Float('Cantidad Actual BAK', store=True)
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
    transf_id = fields.Many2one('wizard.reg.consumo')

    def validar_si_hay_stock_para_el_pedido(self, cantidad_en_stock, cantidad_solicitada):
        hay_stock_para_cubrir_el_pedido = cantidad_solicitada <= cantidad_en_stock

        if not hay_stock_para_cubrir_el_pedido:
            raise ValidationError("La Cantidad ingresada es superior a la Cantidad actual!")

    @api.model
    def create(self, values):
        resultado = super(wizline, self).create(values)
        cantidad_solicitada_del_producto = resultado.product_uom_qty

        if cantidad_solicitada_del_producto != 0:
            cantidad_de_producto_en_stock = resultado.stock_bak
            resultado.validar_si_hay_stock_para_el_pedido(cantidad_de_producto_en_stock,
                                                          cantidad_solicitada_del_producto)

        return resultado

    @api.multi
    def write(self, values):
        super(wizline, self).write(values)

        for record in self:
            cantidad_solicitada_del_producto = values['product_uom_qty'] if 'product_uom_qty' in values else 0.0

            if cantidad_solicitada_del_producto != 0:
                cantidad_de_producto_en_stock = record.stock_bak
                record.validar_si_hay_stock_para_el_pedido(cantidad_de_producto_en_stock,
                                                           cantidad_solicitada_del_producto)

    def obtener_dict_de_productos_y_cantidades(self):
        productos_validos = self.transf_id.obtener_productos_validos_parcial()
        productos_validos_a_mostrar = dict()

        if productos_validos:
            for product_id, cantidad_actual in productos_validos:
                productos_validos_a_mostrar[product_id] = cantidad_actual

        return productos_validos_a_mostrar

    @api.onchange("product_id")
    def onchange_product_id(self):
        productos_validos = self.obtener_dict_de_productos_y_cantidades()
        id_del_producto = self.product_id.id

        if not id_del_producto:
            return {'domain': {'product_id': [('id', 'in', productos_validos.keys())]}}

        else:
            cantidad_del_producto = productos_validos[id_del_producto] if id_del_producto in productos_validos else 0.0

            self.stock = cantidad_del_producto
            self.stock_bak = cantidad_del_producto


class wizard(models.TransientModel):
    _name = "wizard.reg.consumo"

    @api.multi
    def get_domain_orig(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        con_sector = []

        for location in user.stock_location_stock_ids:
            # (not location.sector.id) and  se quita 21/5
            if not location.scrap_location:
                if not location.name == u'Recepciones':
                    con_sector.append(location.id)

        location_ids = con_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]

    @api.multi
    def get_domain_dest(self):
        user = self.env["res.users"].browse([self.env.uid])
        location_ids = [loc.id for loc in user.stock_location_ids]
        wharehouses = self.env['stock.warehouse'].search([
            ('wh_output_stock_loc_id', 'in', location_ids)
        ])

        return [('id', 'in', [wh.wh_output_stock_loc_id.id for wh in wharehouses])]

    location_dest_readonly = fields.Boolean()
    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)
    move_lines = fields.One2many('wizard.reg.consumos.line', inverse_name='transf_id', String='Internal Moves',
                                 copy=True)

    sector_ids = fields.Many2one('categoria', string="Sector")

    @api.one
    @api.constrains('new_location_orig_id')
    def check_user_location_rights(self):
        user_locations = self.env.user.stock_location_ids
        if self.env.user.restrict_locations and \
                self.new_location_orig_id not in user_locations:

            name = self.new_location_orig_id.name
            if type(name) == unicode:
                name = name.encode("utf-8")

            message = (
                          'Ubicación inválida. No puede procesar este movimiento  '
                          'no tiene permisos en "%s". '
                          'Contacte al Administrador.') % name

            raise Warning(message)

    @api.onchange("new_location_orig_id")
    def onchange_new_location_dest_id(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        con_sector = []
        self.move_lines = [(5)]

        for location in user.stock_location_ids:
            if location.scrap_location:
                con_sector.append(location.id)

        if len(con_sector) == 1 and self.new_location_dest_id.id == False:
            self.new_location_dest_id = con_sector[0]

    def obtener_productos_validos(self):
        tengo_datos_para_buscar = self.sector_ids and self.new_location_orig_id
        resultado = False

        if tengo_datos_para_buscar:
            consulta = """
                    SELECT p.id as product_id, sum(sq.qty) as cantidad
                    FROM product_product p
                    INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                    INNER JOIN categoria ct ON ct.id = pt.categoria_id and ct.id in %(sector_ids)s
                    INNER JOIN stock_quant sq ON p.id = sq.product_id AND sq.reservation_id IS NULL AND sq.location_id = %(location_id)s 
                    GROUP BY p.id
            """

            self.env.cr.execute(consulta, {
                'location_id': self.new_location_orig_id.id,
                'sector_ids': tuple(self.sector_ids.ids)
            })

            resultado = self.env.cr.fetchall()

        return resultado


    def obtener_productos_validos_parcial(self):
        tengo_datos_para_buscar = self.sector_ids and self.new_location_orig_id
        resultado = False

        if tengo_datos_para_buscar:
            consulta = """
                    SELECT p.id as product_id, sum(sq.qty) as cantidad
                    FROM product_product p
                    INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                    INNER JOIN categoria ct ON ct.id = pt.categoria_id and ct.id in %(sector_ids)s
                    INNER JOIN stock_quant sq ON p.id = sq.product_id AND sq.reservation_id IS NULL AND sq.location_id = %(location_id)s 
                    GROUP BY p.id
            """

            self.env.cr.execute(consulta, {
                'location_id': self.new_location_orig_id.id,
                'sector_ids': tuple(self.sector_ids.ids)
            })

            resultado = self.env.cr.fetchall()

        return resultado

    def limpiar_lista_de_productos(self):
        self.move_lines = [(6, 0, list())]

    @api.onchange("sector_ids", "new_location_orig_id")
    def onchange_sector_ids_and_new_location_orig_id(self):
        self.limpiar_lista_de_productos()

    @api.model
    @api.one
    def saco_productos(self):
        lineas = self.env["wizard.reg.consumos.line"]

        productos_validos = self.obtener_productos_validos()

        for product_id, cantidad_stock in productos_validos:
            # for item in stock_quants:  'product_uom': item.product_id.uom_id.id,
            lineas.create(
                {
                    'product_id': product_id,
                    'product_qty': 0,
                    'product_uom_qty': 0,
                    'stock': cantidad_stock,
                    'stock_bak': cantidad_stock,
                    'transf_id': self.id
                }
            )
            # 4
            self.write({'move_lines': [(4, x) for x in lineas]})


    @api.multi
    def action_lista_productos(self):

        for line in self.move_lines:
            line.unlink()

            continue

        self.saco_productos()
        value = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.reg.consumo',
            'views': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
            'res_id': self.id,
        }
        return value

    def obtener_productos_repetidos(self):
        lista_de_productos = self.move_lines
        productos_repetidos = str()
        lista_productos_revisados = list()

        for linea in lista_de_productos:
            id_del_producto = linea.product_id.id

            if id_del_producto not in lista_productos_revisados:
                lista_productos_revisados.append(id_del_producto)

            else:
                codigo_del_producto = linea.product_id.code
                nombre_del_producto = linea.product_id.name

                productos_repetidos += '[' + codigo_del_producto + '] ' + nombre_del_producto + '\n'

        return productos_repetidos

    @api.multi
    def action_create_consumo(self):
        productos_repetidos = self.obtener_productos_repetidos()

        if productos_repetidos:
            raise ValidationError(
                "Los siguientes Productos estan repetidos:\n\n%(productos)s" % {'productos': productos_repetidos})

        wharehouses = self.env['stock.warehouse'].search([
            ('wh_output_stock_loc_id', '=', self.new_location_dest_id.id)
        ])

        if len(wharehouses) > 0:
            wharehouse = wharehouses[0]

        if not wharehouse:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Error Configuracion",
                    "text": "No esta configurado correctamente la Ubicación de salida/Consumo",
                    "sticky": False,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": self.new_location_orig_id,
            'location_dest_id': self.new_location_dest_id.id,
            'picking_type_id': wharehouse.out_type_id.id,
            'state': 'draft',
            'sector_id': self.sector_ids.id,
        })

        tengo_algo_en_el_pedido = False

        for line in self.move_lines:
            se_ingreso_este_producto_al_pedido = line.product_qty > 0

            if se_ingreso_este_producto_al_pedido:
                tengo_algo_en_el_pedido = True

                self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_out.id,
                    'picking_type_id': wharehouse.out_type_id.id,
                    'location_id': self.new_location_orig_id.id,
                    'location_dest_id': self.new_location_dest_id.id,
                })

        if not tengo_algo_en_el_pedido:
            raise ValidationError("No hay ninguna Cantidad ingresada!")

        if len(self.move_lines) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Pedidos",
                    "text": "No se encontraron productos para generar pedido",
                    "sticky": False,
                }
            }
        else:

            if picking_out.state == 'draft':
                picking_out.action_confirm()
            if picking_out.state == 'confirmed':
                picking_out.action_assign()
            if picking_out.state == 'assigned':
                transfert_wizard_obj = self.env['stock.transfer_details'].with_context(
                    active_model='stock.picking',
                    active_ids=[picking_out.id],
                    active_id=picking_out.id)
                transfert_wizard = transfert_wizard_obj.create({'picking_id': picking_out.id})
                transfert_wizard.do_detailed_transfer()


wizard()
