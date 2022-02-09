# -*- encoding: utf-8 -*-
from datetime import date, timedelta, datetime
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import tools

class wizard(models.TransientModel):
    _name = "wizard.pedido.consumo.sueros"

    @api.multi
    def get_domain_orig(self):
        # user = self.env["res.users"].browse([self.env.uid])
        # picking_type_ids = user.default_picking_type_ids
        #
        # id = False
        # if len(picking_type_ids) == 1:
        #     dest_id = picking_type_ids.default_location_dest_id
        #     if len(dest_id) == 1:
        #         self.new_location_orig_id = dest_id.id
        # else:
        #     for t in picking_type_ids:
        #         if t.code == u'internal':
        #             id = t.default_location_dest_id.id

        return [('id', '=', 520)]


    @api.multi
    def get_domain_dest(self):

        ids = []
        user = self.env["res.users"].browse([self.env.uid])

        for location in user.stock_location_ids:
            if location.usage == 'internal':
                ids.append(location.id)

        orig_ids = ids[:]

        return [('id', 'in', orig_ids)]


    @api.model
    def _default_datetime(self):
        return datetime.today()

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    fecha_inicial = fields.Datetime('Begin date')
    fecha_final = fields.Datetime('End date', readonly=True, default=_default_datetime)

    inicial = fields.Datetime('fecha inicial', related='fecha_inicial', readonly=True)

    almacen = fields.Many2one('stock.warehouse', related='new_location_dest_id.almacen_id', readonly=True)

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial > self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    @api.onchange("new_location_dest_id")
    def onchange_new_location_dest_id(self):
        # hoy = datetime.today()
        hoy = datetime.today() - timedelta(hours=3)
        self.fecha_inicial = hoy

        # nuevo
        if self.new_location_dest_id.fecha_ultima_reposicion_sueros:
            self.fecha_inicial = self.new_location_dest_id.fecha_ultima_reposicion_sueros
        else:
            self.fecha_inicial = hoy - timedelta(days=7)
            #  fin

    def obtener_stock_actual_del_producto(self, id_de_ubicacion, id_del_product_template):
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', id_de_ubicacion),
            ('product_id.product_tmpl_id', '=', id_del_product_template),
            ('reservation_id', '=', None),
        ])

        stock_actual = sum(quants.mapped('qty'))

        return stock_actual

    @api.multi
    def action_create_picking(self):
        for record in self:
            picking_out = False

            wharehouses = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', '=', self.new_location_dest_id.id)
            ])

            if len(wharehouses) > 0:
                destino_id = wharehouses[0].lot_stock_id
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': u'Notificación',
                    'params': {
                        'title': u'Configuración',
                        'text': u'La ubicación destino presenta algún error de configuración',
                        'sticky': True
                    }
                }

            # *****************


            Ffinal = datetime.today().replace(microsecond=0)

            hoy = datetime.today() - timedelta(hours=3)

            if self.new_location_dest_id.fecha_ultima_reposicion_sueros == str(hoy):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': u'Notificación',
                    'params': {
                        'title': u'Reposición',
                        'text': u'Ya se realizo reposición para la filial en la fecha',
                        'sticky': True
                    }
                }

            if len(wharehouses) > 0:
                wharehouse = wharehouses[0]

            # destino_id.almacen_id.id
            dominio = []
            ubicaciones = self.env['stock.location'].search([
                ('almacen_id', '=', destino_id.almacen_id.id),
            ])

            algo_encontre = False
            for ubicacion in ubicaciones:
                self.env.cr.execute(
                    """
                                SELECT distinct * FROM 
                                sp_reponer_sueros(%(location_destino)s,%(location_origen)s,%(ffecha_i)s,%(ffecha_f)s) 
                                where qty > 0;
                                                 
                           """
                    , {
                        'location_destino': ubicacion.id,
                        'location_origen': int(520),
                        'ffecha_i': self.fecha_inicial,
                        'ffecha_f': str(Ffinal)
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

                    ubicacion_principal = int(520)

                    # DU
                    # ('tipo_de_empaque', '=', 2),
                    # ('presentacion_id', '=', 125)]


                    if primero:
                        ori = ubicacion.name.encode("utf-8")
                        picking_out = self.env['stock.picking'].create({
                            'location_id': int(520),
                            'location_dest_id': self.new_location_dest_id.id,
                            'por_consumo_sueros': True,
                            'picking_type_id': wharehouse.int_type_id.id,
                            'origin': 'Reposición Suero ' + ori + ' : ' + self.fecha_inicial + ' a ' + self.fecha_final
                        })

                        if cantidad_a_reponer > 0:
                            self.env['stock.move'].create({
                                'name': 'Reposición ' + ori,
                                'product_id': producto_id,
                                'product_uom_qty': cantidad_a_reponer,
                                'product_uom': product_uom,
                                'picking_id': picking_out.id,
                                'picking_type_id': wharehouse.int_type_id.id,
                                'lote': '',
                                'location_dest_id': self.new_location_dest_id.id,
                                'location_id': int(520),

                            })
                            # actualizo fecha ultima reposicion

                            self.new_location_dest_id.write(
                                {'fecha_ultima_reposicion_sueros': datetime.today().replace(microsecond=0)})

                        primero = False
                        algo_encontre = True
                        dominio.append(picking_out.id)

                    else:
                        self.env['stock.move'].create({
                            'name': 'Reposición ' + ori,
                            'product_id': producto_id,
                            'product_uom_qty': cantidad_a_reponer,
                            'product_uom': product_uom,
                            'picking_id': picking_out.id,
                            'picking_type_id': wharehouse.int_type_id.id,
                            'lote': '',
                            'location_dest_id': self.new_location_dest_id.id,
                            'location_id': int(520),
                        })

                        # actualizo fecha ultima reposicion
                        self.new_location_dest_id.write(
                            {'fecha_ultima_reposicion_sueros': datetime.today().replace(microsecond=0)})
                if picking_out:
                    picking_out.action_confirm()
                    picking_out.action_assign()

            if not algo_encontre:

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
        #         if picking_out.state == 'draft':
        #             picking_out.action_confirm()
        #             picking_out.action_assign()
        #
                return {
                    'domain': [('id', 'in', dominio)],
                    'name': 'x Consumo Sueros',
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'context': {'tree_view_ref': 'stock.picking.tree'},
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window'}


            # else:
            #     if picking_out:
            #         dominio = picking_out.id
            #
            #     # *****
            #     pendientes = self.env['stock.picking'].search([
            #         ('picking_type_id', '=', wharehouse.int_type_id.id),
            #         ('state', '!=', 'done'),
            #         ('state', '!=', 'cancel'),
            #         ('id', '!=', dominio),
            #         ('por_consumo_sueros', '=', True),
            #         ('location_dest_id', '=', self.new_location_dest_id.id)
            #
            #     ], limit=None)
            #
            #
            #
            #     for pendiente in pendientes:
            #
            #         for linea in pendiente.move_lines:
            #             if linea.state != 'done':
            #                 xproduct_id = linea.product_id.id
            #                 xproduct_uom_qty = linea.product_uom_qty
            #                 xproduct_uom = linea.product_uom.id
            #
            #                 # busco producto en atock_move del pedido , si no lo encuentro lo agrego
            #                 en_pedido = self.env['stock.move'].search([
            #                     ('product_id','=', xproduct_id),
            #                     ('picking_id','=', dominio)
            #                 ], limit=1)
            #
            #                 if xproduct_uom_qty > 0 and not en_pedido:
            #                     self.env['stock.move'].create({
            #                         'name': 'por consumo anterior sueros',
            #                         'product_id': xproduct_id,
            #                         'product_uom_qty': xproduct_uom_qty,
            #                         'product_uom': xproduct_uom,
            #                         'picking_id': dominio,
            #                         'picking_type_id': wharehouse.int_type_id.id,
            #                         'lote': False,
            #                         'location_dest_id': self.new_location_dest_id.id,
            #                         'location_id': int(520),
            #                     })
            #
            #
            #                 cr = self.env.cr
            #                 uid = self.env.uid
            #                 context = self.env.context.copy()
            #
            #                 try:
            #                     self.pool.get('stock.move').action_cancel(cr, uid, linea.id, context)
            #                 except Exception as e:
            #                     continue
            #         try:
            #             self.pool.get('stock.picking').action_cancel(cr, uid, pendiente.id, context)
            #         except Exception as e:
            #             # self.pool.get('stock.picking').do_unreserve(cr, uid, pendiente.id, context)
            #             continue
            #
            #     if picking_out:
            #         # *******
            #         if picking_out.state == 'draft':
            #             picking_out.action_confirm()
            #             picking_out.action_assign()
            #
            #     return {
            #         'domain': [('id', '=', dominio)],
            #         'name': 'x Consumo Sueros',
            #         'view_mode': 'tree,form',
            #         'view_type': 'form',
            #         'context': {'tree_view_ref': 'stock.picking.tree'},
            #         'res_model': 'stock.picking',
            #         'type': 'ir.actions.act_window'}


wizard()
