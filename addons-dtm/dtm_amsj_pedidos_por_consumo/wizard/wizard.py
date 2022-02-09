# -*- encoding: utf-8 -*-
from datetime import date, timedelta, datetime
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import tools

class wizard(models.TransientModel):
    _name = "wizard.pedido.consumo"

    @api.multi
    def get_domain_orig(self):
        user = self.env["res.users"].browse([self.env.uid])
        picking_type_ids = user.default_picking_type_ids

        id = False
        if len(picking_type_ids) == 1:
            dest_id = picking_type_ids.default_location_dest_id
            if len(dest_id) == 1:
                self.new_location_orig_id = dest_id.id
        else:
            for t in picking_type_ids:
                if t.code == u'internal':
                    id = t.default_location_dest_id.id

        return [('id', '=', id)]

    @api.multi
    def get_domain_dest(self):
        hoy = datetime.today() - timedelta(hours=3)
        ids = []
        user = self.env["res.users"].browse([self.env.uid])

        for location in user.stock_location_ids:
            if location.agenda_dia == str(hoy.weekday()) or location.reposicion_multiple:
                if location.origen_location_id:
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
        if self.new_location_dest_id.fecha_ultima_reposicion_farmacia:
            self.fecha_inicial = self.new_location_dest_id.fecha_ultima_reposicion_farmacia
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

            if self.new_location_dest_id.fecha_ultima_reposicion_farmacia == str(hoy):
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

            self.env.cr.execute(
                """
                            SELECT distinct * FROM 
                            sp_reponer(%(location_destino)s,%(location_origen)s,%(ffecha_i)s,%(ffecha_f)s) 
                            where qty > 0;
                                             
                    """
                , {
                    'location_destino': destino_id.id,
                    'location_origen': self.new_location_dest_id.origen_location_id.id,
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

                ubicacion_principal = self.env['stock.location'].search([
                    ('almacen_id', '=', wharehouses[0].id),
                    ('principal_del_expendio', '=', True)
                ])

                # DU
                # ('tipo_de_empaque', '=', 2),
                # ('presentacion_id', '=', 125)]

                if ubicacion_principal:
                    ubicacion_principal = ubicacion_principal[0]

                if primero:

                    if not wharehouses:
                        texto = "Ubicacion : " + self.new_location_dest_id.complete_name + ", No esta definida como Entrada"
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'action_warn',
                            'name': 'Notificación',
                            'params': {
                                'title': 'Error Configuracion',
                                'text': texto,
                                'sticky': True
                            }
                        }

                    if len(wharehouses) > 0:
                        wharehouse = wharehouses[0]

                    picking_out = self.env['stock.picking'].create({
                        'location_id': self.new_location_dest_id.origen_location_id.id,
                        'location_dest_id': self.new_location_dest_id.id,
                        'por_consumo': True,
                        'picking_type_id': wharehouse.int_type_id.id,
                        'origin': 'Reposición por consumo ' + self.fecha_inicial + ' a ' + self.fecha_final
                    })

                    if cantidad_a_reponer > 0:
                        self.env['stock.move'].create({
                            'name': 'Reposición por consumo',
                            'product_id': producto_id,
                            'product_uom_qty': cantidad_a_reponer,
                            'product_uom': product_uom,
                            'picking_id': picking_out.id,
                            'picking_type_id': wharehouse.int_type_id.id,
                            'lote': lote,
                            'location_dest_id': self.new_location_dest_id.id,
                            'location_id': self.new_location_dest_id.origen_location_id.id,

                        })
                        # actualizo fecha ultima reposicion

                        self.new_location_dest_id.write(
                            {'fecha_ultima_reposicion_farmacia': datetime.today().replace(microsecond=0)})

                    primero = False

                else:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out.id,
                        'picking_type_id': wharehouse.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': self.new_location_dest_id.id,
                        'location_id': self.new_location_dest_id.origen_location_id.id,
                    })

                    # actualizo fecha ultima reposicion
                    self.new_location_dest_id.write(
                        {'fecha_ultima_reposicion_farmacia': datetime.today().replace(microsecond=0)})


            if primero:

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
                if picking_out:
                    dominio = picking_out.id

                # *****
                pendientes = self.env['stock.picking'].search([
                    ('picking_type_id', '=', wharehouse.int_type_id.id),
                    ('state', '!=', 'done'),
                    ('state', '!=', 'cancel'),
                    ('id', '!=', dominio),
                    ('location_id', '=', self.new_location_dest_id.origen_location_id.id),
                    ('location_dest_id', '=', self.new_location_dest_id.id)

                ], limit=None)

                for pendiente in pendientes:
                    x = 0

                    productos_en_pedido = self.env['stock.move'].search([

                        ('picking_id', '=', dominio)
                    ])

                    for linea in pendiente.move_lines:

                        if linea.state != 'done':
                            xproduct_id = linea.product_id.id
                            xproduct_uom_qty = linea.product_uom_qty
                            xproduct_uom = linea.product_uom.id

                            principio_activo_id = linea.product_id.product_tmpl_id.principio_activo_id.id
                            forma_farmaceutica_id = linea.product_id.product_tmpl_id.forma_farmaceutica_id.id
                            concentracion_valor = linea.product_id.product_tmpl_id.concentracion_valor
                            concentracion_unidad = linea.product_id.product_tmpl_id.concentracion_unidad.id or False
                            tipo_de_empaque = linea.product_id.product_tmpl_id.tipo_de_empaque.id
                            rmc = linea.product_id.product_tmpl_id.rmc

                            # busco producto en atock_move del pedido , si no lo encuentro lo agrego

                            encontrado = False
                            for prod in productos_en_pedido:
                                if (principio_activo_id == prod.product_id.product_tmpl_id.principio_activo_id.id and \
                                         forma_farmaceutica_id == prod.product_id.product_tmpl_id.forma_farmaceutica_id.id and \
                                         concentracion_valor == prod.product_id.product_tmpl_id.concentracion_valor and \
                                         concentracion_unidad == prod.product_id.product_tmpl_id.concentracion_unidad.id and \
                                         tipo_de_empaque == prod.product_id.product_tmpl_id.tipo_de_empaque.id and \
                                         rmc == prod.product_id.product_tmpl_id.rmc):

                                    encontrado = True
                                    # if xproduct_uom_qty > 0 and not en_pedido:

                            if not encontrado:
                                self.env['stock.move'].create({
                                    'name': 'Pendiente anterior',
                                    'product_id': xproduct_id,
                                    'product_uom_qty': xproduct_uom_qty,
                                    'product_uom': xproduct_uom,
                                    'picking_id': dominio,
                                    'picking_type_id': wharehouse.int_type_id.id,
                                    'lote': False,
                                    'location_dest_id': self.new_location_dest_id.id,
                                    'location_id': self.new_location_dest_id.origen_location_id.id,
                                })

                            cr = self.env.cr
                            uid = self.env.uid
                            context = self.env.context.copy()

                            # try:
                            #     self.pool.get('stock.move').action_cancel(cr, uid, linea.id, context)
                            # except Exception as e:
                            #     continue
                    try:
                        self.pool.get('stock.picking').action_cancel(cr, uid, pendiente.id, context)
                    except Exception as e:
                        # self.pool.get('stock.picking').do_unreserve(cr, uid, pendiente.id, context)
                        continue

                if picking_out:
                    # *******
                    if picking_out.state == 'draft':
                        picking_out.action_confirm()
                        picking_out.action_assign()
                        
                return {
                    'domain': [('id', '=', dominio)],
                    'name': 'x Consumo',
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    'context': {'tree_view_ref': 'stock.picking.tree'},
                    'res_model': 'stock.picking',
                    'type': 'ir.actions.act_window'}


wizard()
