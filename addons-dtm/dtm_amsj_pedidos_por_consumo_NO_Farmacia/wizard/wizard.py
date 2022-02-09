# -*- encoding: utf-8 -*-
from datetime import date, timedelta, datetime
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class wizard(models.TransientModel):
    _name = "wizard.pedido"

    @api.model
    def _default_datetime(self):
        now = datetime.today()
        return now

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
        orig_ids = []
        user = self.env["res.users"].browse([self.env.uid])
        for default_picking_type in user.default_picking_type_ids:
            if default_picking_type.code == 'incoming':
                if default_picking_type.warehouse_id != 26:
                    orig_ids.append(default_picking_type.default_location_dest_id.id)

        return [('id', '=', orig_ids)]

    # @api.model
    # def _default_date(self):
    #     return date.today() - timedelta(days=1)

    # @api.multi
    def get_ubicaciones_origen(self):
        user = self.env["res.users"].browse([self.env.uid])
        picking_type_ids = user.default_picking_type_ids

        ubic_origen_por_defecto = set()
        if len(picking_type_ids) == 1:
            ubic_origen_por_defecto.add(picking_type_ids.default_location_src_id)
        else:
            for ubic_propia in picking_type_ids:
                ubic_origen_por_defecto.add(ubic_propia.default_location_src_id)
        return list(ubic_origen_por_defecto)

    def get_ubicaciones_origen_STOCK(self):
        user = self.env["res.users"].browse([self.env.uid])
        picking_type_ids = user.stock_location_stock_ids

        ubic_origen_por_defecto = set()
        # if len(picking_type_ids) == 1:
        #     ubic_origen_por_defecto.add(picking_type_ids.default_location_src_id)
        # else:
        for ubic_propia in picking_type_ids:
            ubic_origen_por_defecto.add(ubic_propia.id)
        return list(ubic_origen_por_defecto)


    @api.multi
    def get_domain_sector(self):
        ubic_origen_por_defecto = self.get_ubicaciones_origen_STOCK()

        ids = list()
        if ubic_origen_por_defecto:
            for ubicacion in ubic_origen_por_defecto:
                u = self.env['stock.location'].search([('id', '=', ubicacion)])
                if u.sector:
                    if u.sector.id <> 17:
                        ids.append(u.sector.id)

        return [('id', 'in', ids)]

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    # fecha_inicial = fields.Date('Begin date')
    # fecha_final = fields.Date('End date', default=date.today())

    fecha_inicial = fields.Datetime('Begin date')
    fecha_final = fields.Datetime('End date', default=_default_datetime)

    inicial = fields.Datetime('fecha inicial', related='fecha_inicial')

    almacen = fields.Many2one('stock.warehouse', related='new_location_dest_id.almacen_id', readonly=True)

    sector_ids = fields.Many2one('categoria', string="Sector", domain=get_domain_sector)

    edita_fecha = fields.Boolean(string="fecha", default=False)

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial > self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    @api.onchange("new_location_dest_id")
    def onchange_new_location_dest_id(self):

        if self.new_location_dest_id:
            if self.sector_ids.name == 'Deposito':
                inicial = self.new_location_dest_id.fecha_ultima_reposicion_deposito

            if self.sector_ids.name == 'Proveeduria' or self.sector_ids.id == 19:
                inicial = self.new_location_dest_id.fecha_ultima_reposicion_proveeduria

            if self.sector_ids.name == 'Laboratorio':
                inicial = self.new_location_dest_id.fecha_ultima_reposicion_laboratorio

            if self.sector_ids.name == 'Hemoterapia':
                inicial = self.new_location_dest_id.fecha_ultima_reposicion_hemoterapia

            if inicial:
                self.fecha_inicial = inicial
            else:
                self.edita_fecha = True
                self.fecha_inicial = datetime.today() - timedelta(days=7)
                #  fin

        hoy = date.today()
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        for location in user.stock_location_ids:
            if location.origen_location_id:
                if location.agenda_dia == str(hoy.weekday()):
                    if self.new_location_dest_id.id is False:
                        self.new_location_dest_id = location.id
                        # nuevo

    @api.multi
    def action_create_picking(self):
        for record in self:
            wharehouses = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', '=', record.new_location_dest_id.id)
            ])

            # origen

            # ubicacion_consumo_id = wharehouses.wh_output_stock_loc_id.id
            sector_id = record.sector_ids.id

            ubicacion_origen = wharehouses.lot_stock_id
            posibles_ubicaciones_origen = record.get_ubicaciones_origen()
            for posible_ubic in posibles_ubicaciones_origen:
                if posible_ubic.sector == record.sector_ids:
                    ubicacion_origen = posible_ubic
                    break

            # *****************
            # destino_id = wharehouses[0].in_type_id
            hoy = datetime.strptime(str(datetime.today().replace(microsecond=0)), DEFAULT_SERVER_DATETIME_FORMAT)

            Ffinal = hoy

            #   12 / 08
            if record.new_location_dest_id:

                if record.sector_ids.name == 'Deposito':
                    inicial = record.new_location_dest_id.fecha_ultima_reposicion_deposito

                if record.sector_ids.name == 'Proveeduria' or record.sector_ids.id == 19:
                    inicial = record.new_location_dest_id.fecha_ultima_reposicion_proveeduria

                if record.sector_ids.name == 'Laboratorio':
                    inicial = record.new_location_dest_id.fecha_ultima_reposicion_laboratorio

                if record.sector_ids.name == 'Hemoterapia':
                    inicial = record.new_location_dest_id.fecha_ultima_reposicion_hemoterapia

                if inicial:
                    record.fecha_inicial = inicial
                else:
                    record.edita_fecha = True
                    record.fecha_inicial = datetime.today() - timedelta(days=7)
                    #  fin
            #
            if not Ffinal:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'action_warn',
                    'name': 'Notificación',
                    'params': {
                        'title': 'Pedidos',
                        'text': 'No se pudo generar pedido , intente nuevamente',
                        'sticky': True
                    }
                }

            # si es centro de materiales
            if self.new_location_dest_id.almacen_id.id == 41:
                self.env.cr.execute(

                    """
                      SELECT 'CDM' as destino,product_id, sum(product_uom_qty) as cantidad, product_uom ,p.product_tmpl_id
                            FROM stock_move
                            INNER JOIN product_product p ON p.id = stock_move.product_id
                            INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                            INNER JOIN stock_location l ON l.id = stock_move.location_id
                            where (stock_move.date >= timestamp %(ffecha_i)s AND stock_move.date < timestamp %(ffecha_f)s)  AND
                                    l.almacen_id = %(almacen)s AND
                                    (pt.familia_id <> 73 or pt.familia_id isnull) AND
                                    (coalesce(stock_move.cancelado,false)) = false AND
                                    pt.categoria_id = %(sector)s  AND stock_move.inventory_id IS NULL
                            group by  product_id , product_uom ,p.product_tmpl_id
                            
                            ;
                    """

                    , {
                        'almacen': record.new_location_dest_id.almacen_id.id,
                        'sector': sector_id,
                        'ffecha_i': record.fecha_inicial,
                        'ffecha_f': Ffinal
                    }
                )
            else:
                self.env.cr.execute(

                    """
                           SELECT l.name,product_id, sum(product_uom_qty) as cantidad, product_uom ,p.product_tmpl_id
                            FROM stock_move
                            INNER JOIN product_product p ON p.id = stock_move.product_id
                            INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                            INNER JOIN stock_location l ON l.id = stock_move.location_id
                            INNER JOIN stock_location sl ON sl.id = stock_move.location_dest_id
                            where (stock_move.date >= timestamp %(ffecha_i)s AND stock_move.date < timestamp %(ffecha_f)s) AND
                                    l.almacen_id = %(almacen)s AND 
                                    (coalesce(stock_move.cancelado,false)) = false AND
                                    (pt.familia_id <> 73 or pt.familia_id isnull) AND
                                    (coalesce(sl.scrap_location,false) = true OR sl.usage = 'customer') AND
                                    pt.categoria_id = %(sector)s  AND stock_move.inventory_id IS NULL
                            group by l.name , product_id , product_uom ,p.product_tmpl_id
                            order by l.name;
    
                    """

                    , {
                        'almacen': record.new_location_dest_id.almacen_id.id,
                        'sector': sector_id,
                        'ffecha_i': record.fecha_inicial,
                        'ffecha_f': Ffinal
                    }
                )

            resultado = self.env.cr.fetchall()
            primero = True
            origen_consumo_ant = ''
            picking_out = False

            for tupla in resultado:
                origen_consumo = tupla[0]
                producto_id = tupla[1]
                cantidad_a_reponer = tupla[2]
                product_uom = tupla[3]
                product_template_id = tupla[4]

                # controlo maximo
                stock_maximo_id = self.env['ubicacion.stockcritico'].search(
                    [('ubicacion_id', '=', record.new_location_dest_id.id),
                     ('product_tmpl_id', '=', product_template_id)
                     ], limit=1)

                stock_actual = record.obtener_stock_actual_del_producto(record.new_location_dest_id.id,
                                                                        product_template_id)

                if stock_maximo_id:
                    cantidad_maxima = stock_maximo_id.stock_critico

                    if stock_actual < cantidad_maxima:
                        cantidad_a_reponer = cantidad_maxima - stock_actual
                    else:
                        if stock_actual >= cantidad_maxima:
                            cantidad_a_reponer = 0
                        else:
                            cantidad_a_reponer = tupla[2]
                else:
                    cantidad_a_reponer = tupla[2]

                if primero:
                    if not wharehouses:
                        texto = "Ubicacion : " + record.new_location_dest_id.complete_name + ", No esta definida como Entrada"
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

                    if cantidad_a_reponer > 0:
                        picking_out = self.env['stock.picking'].create({
                            # 'location_id': 520,
                            'location_id': ubicacion_origen.id,
                            'location_dest_id': record.new_location_dest_id.id,
                            'picking_type_id': wharehouse.int_type_id.id,
                            'por_consumo': True,
                            'origin': u'Reposición por consumo: ' + origen_consumo
                        })

                        record.crear_movimiento(
                            u'Reposición por consumo: ' + origen_consumo,
                            producto_id,
                            cantidad_a_reponer,
                            product_uom,
                            picking_out.id,
                            wharehouse.int_type_id.id,
                            record.new_location_dest_id.id,
                            ubicacion_origen.id,
                        )

                    primero = False
                    origen_consumo_ant = origen_consumo

                else:
                    if origen_consumo_ant == origen_consumo:
                        if not picking_out:
                            if cantidad_a_reponer > 0:
                                picking_out = self.env['stock.picking'].create({
                                    # 'location_id': 520,
                                    'location_id': ubicacion_origen.id,
                                    'location_dest_id': record.new_location_dest_id.id,
                                    'picking_type_id': wharehouse.int_type_id.id,
                                    'por_consumo': True,
                                    'origin': u'Reposición por consumo: ' + origen_consumo
                                })

                        if cantidad_a_reponer > 0:
                            record.crear_movimiento(
                                u'Reposición por consumo: ' + origen_consumo,
                                producto_id,
                                cantidad_a_reponer,
                                product_uom,
                                picking_out.id,
                                wharehouse.int_type_id.id,
                                record.new_location_dest_id.id,
                                ubicacion_origen.id,
                            )
                    else:

                        if cantidad_a_reponer > 0:
                            picking_out = self.env['stock.picking'].create({
                                'location_id': ubicacion_origen.id,
                                'location_dest_id': record.new_location_dest_id.id,
                                'picking_type_id': wharehouse.int_type_id.id,
                                'por_consumo': True,
                                'origin': u'Reposición por consumo: ' + origen_consumo
                            })

                            record.crear_movimiento(
                                u'Reposición por consumo: ' + origen_consumo,
                                producto_id,
                                cantidad_a_reponer,
                                product_uom,
                                picking_out.id,
                                wharehouse.int_type_id.id,
                                record.new_location_dest_id.id,
                                ubicacion_origen.id,
                            )

                        origen_consumo_ant = origen_consumo

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

                # actualizo fecha ultima reposicion

                hoy = datetime.strptime(str(datetime.today().replace(microsecond=0)), DEFAULT_SERVER_DATETIME_FORMAT)

                # if self.sector_ids.id == 18:
                #     self.new_location_dest_id.write({'fecha_ultima_reposicion_deposito': hoy})
                # else:
                #     self.new_location_dest_id.write({'fecha_ultima_reposicion_proveeduria': hoy})

                if self.sector_ids.name == 'Deposito':
                    self.new_location_dest_id.write({'fecha_ultima_reposicion_deposito': hoy})

                if self.sector_ids.id == 19:
                    self.new_location_dest_id.write({'fecha_ultima_reposicion_proveeduria': hoy})

                if self.sector_ids.name == 'Laboratorio':
                    self.new_location_dest_id.write({'fecha_ultima_reposicion_laboratorio': hoy})

                #
                if self.sector_ids.name == 'Hemoterapia':
                    self.new_location_dest_id.write({'fecha_ultima_reposicion_hemoterapia': hoy})

                if picking_out:

                    pendientes = []
                    # *****  faltan pruebas
                    # pendientes = self.env['stock.picking'].search([
                    #     ('picking_type_id', '=', wharehouse.int_type_id.id),
                    #     ('state', '!=', 'done'),
                    #     ('state', '!=', 'cancel'),
                    #     ('id', '!=', picking_out.id),
                    #     ('location_id', '=', ubicacion_origen.id),
                    #     ('location_dest_id', '=', self.new_location_dest_id.id)
                    #
                    # ], limit=None)

                    for pendiente in pendientes:

                        for linea in pendiente.move_lines:
                            if linea.state != 'done':
                                xproduct_id = linea.product_id.id
                                xproduct_uom_qty = linea.product_uom_qty
                                xproduct_uom = linea.product_uom.id

                                if xproduct_uom_qty > 0:


                                    # buscar en picking_out  el producto
                                    #  picking_out.move_lines  --> aca estan los productos
                                    #  product_qty  , product_id
                                    cantidad_ant = 0
                                    for xLinea in picking_out.move_lines:
                                        if xLinea.product_id.id == linea.product_id.id:
                                            xMoveLine_Id = xLinea.id
                                            cantidad_ant = xLinea.product_uom_qty

                                    cantidad_total = cantidad_ant + linea.product_uom_qty


                                    #  buscar stock maximo
                                    # controlo maximo
                                    stock_maximo_id = self.env['ubicacion.stockcritico'].search(
                                        [('ubicacion_id', '=', record.new_location_dest_id.id),
                                         ('product_tmpl_id', '=', linea.product_id.product_tmpl_id.id)
                                         ], limit=1)

                                    stock_actual = record.obtener_stock_actual_del_producto(
                                        record.new_location_dest_id.id,
                                        product_template_id)

                                    if stock_maximo_id:
                                        cantidad_maxima = stock_maximo_id.stock_critico

                                        if stock_actual < cantidad_maxima:
                                            cantidad_a_reponer = cantidad_maxima - stock_actual
                                        else:
                                            if stock_actual >= cantidad_maxima:
                                                cantidad_a_reponer = 0
                                            else:
                                                cantidad_a_reponer = xproduct_uom_qty
                                    else:
                                        cantidad_a_reponer = cantidad_total

                                    if cantidad_ant > 0:
                                         # en lugar de hacer un create , update si existe
                                         line_move = self.env['stock.move'].search(
                                             [('id', '=', xMoveLine_Id)])
                                         line_move.write({'product_uom_qty': cantidad_a_reponer})

                                    else:
                                        self.env['stock.move'].create({
                                            'name': linea.origin or u'x Consumo Anterior',
                                            'product_id': xproduct_id,
                                            'product_uom_qty': cantidad_a_reponer,
                                            'product_uom': xproduct_uom,
                                            'picking_id': picking_out.id,
                                            'picking_type_id': wharehouse.int_type_id.id,
                                            'lote': False,
                                            'location_dest_id': self.new_location_dest_id.id,
                                            'location_id':  ubicacion_origen.id,
                                        })

                                cr = self.env.cr
                                uid = self.env.uid
                                context = self.env.context.copy()

                                self.pool.get('stock.move').action_cancel(cr, uid, linea.id, context)

                        self.pool.get('stock.picking').action_cancel(cr, uid, pendiente.id, context)

                    return {
                        'domain': [('id', '=', picking_out.id)],
                        'name': 'x Consumo',
                        'view_mode': 'tree,form',
                        'view_type': 'form',
                        'context': {'tree_view_ref': 'stock.picking.tree'},
                        'res_model': 'stock.picking',
                        'type': 'ir.actions.act_window'}
                else:
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

    def obtener_stock_actual_del_producto(self, id_de_ubicacion, id_del_product_template):
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', id_de_ubicacion),
            ('product_id.product_tmpl_id', '=', id_del_product_template),
            ('reservation_id', '=', None),
        ])

        stock_actual = sum(quants.mapped('qty'))

        return stock_actual

    def crear_movimiento(self, name, product_id, product_uom_qty, product_uo,
                         picking_id, picking_type_id, location_dest_id, location_id):

        self.env['stock.move'].create({
            'name': name,
            'product_id': product_id,
            'product_uom_qty': product_uom_qty,
            'product_uom': product_uo,
            'picking_id': picking_id,
            'picking_type_id': picking_type_id,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
        })


wizard()
