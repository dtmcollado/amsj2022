# -*- encoding: utf-8 -*-
from datetime import date, timedelta, datetime
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError


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

        ids = []
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        # ids = [location.id for location in user.stock_location_ids]
        for location in user.stock_location_ids:
            if location.origen_location_id:
                ids.append(location.id)

        orig_ids = ids[:]  # list.copy se agregó en python 3.3

        return [('id', 'in', orig_ids)]

    @api.model
    def _default_date(self):
        return date.today() - timedelta(days=7)

    @api.model
    def _default_date_final(self):
        return date.today() - timedelta(days=1)

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    fecha_inicial = fields.Date('Begin date', default=_default_date)
    fecha_final = fields.Date('End date', default=_default_date_final)

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial > self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    @api.onchange("new_location_dest_id")
    def onchange_new_location_dest_id(self):
        hoy = date.today()
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        for location in user.stock_location_ids:
            if location.origen_location_id:
                if location.agenda_dia == str(hoy.weekday()):
                    if self.new_location_dest_id.id is False:
                        self.new_location_dest_id = location.id



    @api.multi
    def action_create_picking(self):
        # ejecutar sql para sacar consumos de productos en el almacen destino
        #  los productos tienen que tener stock en el almacen origen.
        #  ver tema categoria.

        #  origen_location_id


        picking_out = False

        # sacar ubicaciones que tienen geosalud
        # ver de usar sucursal_amsj 

        # GEOSALUD

        sector_amsj = '1'
        subsector_amsj = '3'
        sucursal_amsj = '3'


        self.fecha_inicial = datetime.today() - timedelta(days=7)
        self.fecha_final = datetime.today() + timedelta(days=1)

        fecha_desde = self.fecha_inicial
        fecha_hasta = self.fecha_final



        sql = """select  
            CONVERT(varchar,[Código Geosalud]) as codigo_geosalud,
            CONVERT(varchar,[Cantidad]) as cantidad,CONVERT(varchar,[Nombre Medicamento])  as nombre 
            from CONSUMOS_GEOSALUD 
            where
             CONVERT(varchar,[Número Sector]) ='%s' and
             CONVERT(varchar,[Número Subsector]) ='%s' and
             [Fecha de Consumo] >= CONVERT(datetime,'%s',120) and
             [Fecha de Consumo] < CONVERT(datetime,'%s',120) and
              CONVERT(varchar,[Número de Expendio]) ='%s'""" % (
            sector_amsj, subsector_amsj, fecha_desde, fecha_hasta, sucursal_amsj)

        SERV = self.pool.get('connector.sqlserver').search(self._cr, self._uid, [('name', '=', "amsj")])
        servidor_SQL = self.pool.get('connector.sqlserver').browse(self._cr, self._uid, SERV, self._context)
        conn = servidor_SQL.connect()
        if conn:
            cursor = servidor_SQL.getNewCursor(conn)
            cursor.execute(sql)

            prods = dict()
            lineas = list()
            self.log = " "
            row = cursor.fetchone()

            while row:

                codigo_geosalud = row[0]
                cantidad_linea = float(row[1])
                productos = self.env['product.product'].search([
                    ('codigo_geosalud', '=', codigo_geosalud),
                    ('categoria_id', '=', 17)])

                if productos:
                    wharehouses = self.env['stock.warehouse'].search([('id', '=', 24)])
                    wharehouse = wharehouses[0]

                    if not wharehouse:
                       return {
                           'type': 'ir.actions.client',
                           'tag': 'action_warn',
                           'name': 'Notificación',
                           'params': {
                               "title": "Error Configuracion",
                               "text": "No esta configurado correctamente la Ubicación de salida/Consumo",
                               "sticky": True,
                           }
                       }

                    picking_out = self.env['stock.picking'].create({
                        "location_id": 497,
                        'location_dest_id': 758,
                        'picking_type_id': wharehouse.out_type_id.id,
                        'state': 'draft',
                    })

                for producto in productos:
                    # registrar consumo
                    self.env['stock.move'].create({
                        'name': producto.name,
                        'product_id': producto.id,
                        'product_uom_qty': cantidad_linea,
                        'product_uom': producto.uom_id.id,
                        'picking_id': picking_out.id,
                        'picking_type_id': wharehouse.out_type_id.id,
                        'location_id': 497,
                        'location_dest_id': 758,

                    })

                if productos:
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

                row = cursor.fetchone()

            # *****************************************************
            # ##################################################

        wharehouses = self.env['stock.warehouse'].search([
            ('wh_input_stock_loc_id', '=', self.new_location_dest_id.id)
        ])

        # *****************
        destino_id = wharehouses[0].lot_stock_id

        self.env.cr.execute(
            """
                    SELECT * FROM 
                    sp_reponer(%(location_destino)s,%(location_origen)s,%(ffecha_i)s,%(ffecha_f)s) 
                    where stock = 1;
                                          
                """
            , {
                'location_destino': destino_id.id,
                'location_origen': self.new_location_dest_id.origen_location_id.id,
                'ffecha_i': self.fecha_inicial,
                'ffecha_f': self.fecha_final
            }
        )

        resultado = self.env.cr.fetchall()
        primero = True
        for tupla in resultado:
            producto_id = tupla[0]
            product_uom = tupla[2]
            lote = tupla[3]
            vencimiento = tupla[4]
            cantidad_a_reponer = tupla[5]
            disponible = tupla[6]

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
                    'picking_type_id': wharehouse.int_type_id.id,
                    'origin': 'Reposición por consumo'
                })

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
        #  pedido sin stock

        self.env.cr.execute(
            """
                        SELECT * FROM 
                        sp_reponer(%(location_destino)s,%(location_origen)s,%(ffecha_i)s,%(ffecha_f)s) 
                        where stock = 0;

                    """
            , {
                'location_destino': destino_id.id,
                'location_origen': self.new_location_dest_id.origen_location_id.id,
                'ffecha_i': self.fecha_inicial,
                'ffecha_f': self.fecha_final
            }
        )

        resultado = self.env.cr.fetchall()
        primero_2 = True
        for tupla in resultado:
            producto_id = tupla[0]
            product_uom = tupla[2]
            lote = tupla[3]
            vencimiento = tupla[4]
            cantidad_a_reponer = tupla[5]
            disponible = tupla[6]

            if primero_2:

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

                picking_out2 = self.env['stock.picking'].create({
                    'location_id': self.new_location_dest_id.origen_location_id.id,
                    'location_dest_id': self.new_location_dest_id.id,
                    'picking_type_id': wharehouse.int_type_id.id,
                    'origin': 'Reposición por consumo',
                    'note': ' SIN STOCK a la fecha de armar pedido'
                })

                self.env['stock.move'].create({
                    'name': 'Reposición por consumo',
                    'product_id': producto_id,
                    'product_uom_qty': cantidad_a_reponer,
                    'product_uom': product_uom,
                    'picking_type_id': wharehouse.int_type_id.id,
                    'picking_id': picking_out2.id,
                    'lote': lote,
                    'location_dest_id': self.new_location_dest_id.id,
                    'location_id': self.new_location_dest_id.origen_location_id.id,
                })



                primero_2 = False

            else:
                self.env['stock.move'].create({
                    'name': 'Reposición por consumo SIN STOCK',
                    'product_id': producto_id,
                    'product_uom_qty': cantidad_a_reponer,
                    'product_uom': product_uom,
                    'picking_id': picking_out2.id,
                    'picking_type_id': wharehouse.int_type_id.id,
                    'lote': lote,
                    'location_dest_id': self.new_location_dest_id.id,
                    'location_id': self.new_location_dest_id.origen_location_id.id,
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
            if picking_out:
                dominio = picking_out.id
            else:
                dominio = picking_out2.id
            return {
                'domain': [('id', '=', dominio)],
                'name': 'x Consumo',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.picking.tree'},
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window'}


wizard()
