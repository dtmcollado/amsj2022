# -*- encoding: utf-8 -*-
from datetime import date, timedelta, datetime
from openerp import models, fields, api, tools
from openerp.exceptions import ValidationError


class wizard(models.TransientModel):
    _name = "wizard.pedido.consumo.du"

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
        user = self.env["res.users"].browse([self.env.uid])
        # ids = [location.id for location in user.stock_location_ids]
        for location in user.stock_location_ids:
            if location.usage == 'internal' and not location.scrap_location:
                ids.append(location.id)

        orig_ids = ids[:]  # list.copy se agregó en python 3.3

        return [('id', 'in', orig_ids)]

    @api.model
    def _default_datetime(self):
        now = datetime.today()
        return now

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    fecha_inicial = fields.Datetime('Begin date')
    fecha_final = fields.Datetime('End date', readonly=True, default=_default_datetime)

    inicial = fields.Datetime('fecha inicial', related='fecha_inicial', readonly=True)

    @api.multi
    @api.onchange("new_location_dest_id")
    def onchange_fechas(self):
        hoy = datetime.today()
        self.fecha_inicial = datetime.today()

        # nuevo
        if self.new_location_dest_id.fecha_ultima_reposicion_du:
            self.fecha_inicial = self.new_location_dest_id.fecha_ultima_reposicion_du
        else:
            self.fecha_inicial = datetime.today() - timedelta(days=7)
            #  fin
        # dias = False
        # if self.new_location_dest_id.reponer_ids:
        #     for i in self.new_location_dest_id.reponer_ids:
        #          # import ipdb; ipdb.set_trace()  # breakpoint 70913344 //
        #          print i.sector
        #          if i.sector.id == 17 and len(i.sector)>1:
        #             dias = i.dias[0]
        #
        #          if i.sector.id == 17 and len(i.sector)==1:
        #             dias = i.dias
        #
        #
        #
        # if dias:
        #     self.fecha_inicial=date.today() - timedelta(days=int(dias))
        #
        # else:
        #     self.fecha_inicial=date.today() - timedelta(days=7)

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial > self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    # @api.onchange("new_location_dest_id")
    # def onchange_new_location_dest_id(self):
    #     hoy = date.today()
    #     user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
    #     for location in user.stock_location_ids:
    #         if location.origen_location_id:
    #             if location.agenda_dia == str(hoy.weekday()):
    #                 if self.new_location_dest_id.id is False:
    #                     self.new_location_dest_id = location.id

    @api.multi
    def action_create_picking(self):
        # ejecutar sql para sacar consumos de productos en el almacen destino
        #  los productos tienen que tener stock en el almacen origen.
        #  ver tema categoria.

        #  origen_location_id

        Ffinal = datetime.today().replace(microsecond=0)

        hoy = datetime.today().replace(microsecond=0)

        picking_out = False

        # sacar ubicaciones que tienen geosalud
        # ver de usar sucursal_amsj

        # GEOSALUD

        # *****************************************************
        # ##################################################

        # *****************
        destino_id = self.new_location_dest_id

        self.env.cr.execute(
            """
                    SELECT * FROM 
                        sp_reponer_DU(%(location_destino)s,%(location_origen)s,%(ffecha_i)s,%(ffecha_f)s) 
                    ;
                                          
                """
            , {
                'location_destino': destino_id.id,
                'location_origen': 557,
                'ffecha_i': self.fecha_inicial,
                'ffecha_f': str(Ffinal)
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

            # producto = self.env['product.product'].search([
            #     ('id', '=', producto_id),
            #     ('tipo_de_empaque', '=', 2),
            #     ('presentacion_id', '=', 125)
            # ])

            producto = self.env['product.product'].search([
                ('id', '=', producto_id),

            ])

            # DU
            # ('tipo_de_empaque', '=', 2),
            # ('presentacion_id', '=', 125)]

            ubicacion_principal = self.new_location_dest_id

            # busco stock maximo

            wharehouse = self.new_location_dest_id.almacen_id
            if primero:
                if cantidad_a_reponer:
                    picking_out = self.env['stock.picking'].create({
                        'location_id': self.new_location_dest_id.origen_location_id.id,
                        'location_dest_id': self.new_location_dest_id.id,
                        'picking_type_id': wharehouse.int_type_id.id,
                        'sector_id': int(17),
                        'origin': 'Reposición por consumo DU'
                    })

                    primero = False

                if cantidad_a_reponer > 0:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo DU',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out.id,
                        'picking_type_id': wharehouse.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': self.new_location_dest_id.id,
                        'location_id': 557,

                    })



            else:
                if cantidad_a_reponer > 0:
                    self.env['stock.move'].create({
                        'name': 'Reposición por consumo DU',
                        'product_id': producto_id,
                        'product_uom_qty': cantidad_a_reponer,
                        'product_uom': product_uom,
                        'picking_id': picking_out.id,
                        'picking_type_id': wharehouse.int_type_id.id,
                        'lote': lote,
                        'location_dest_id': self.new_location_dest_id.id,
                        'location_id': 557,
                    })

        if primero:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    'title': 'Pedidos',
                    'text': 'No se encontraron productos para generar pedido DU',
                    'sticky': True
                }
            }
        else:
            # actualizo fecha ultima reposicion

            self.new_location_dest_id.write(
                {'fecha_ultima_reposicion_du': datetime.today().replace(microsecond=0)})

            if picking_out:
                if picking_out.state == 'draft':
                    picking_out.action_confirm()
                    picking_out.action_assign()
                    dominio = picking_out.id

            return {
                'domain': [('id', '=', dominio)],
                'name': 'x Consumo DU',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.picking.tree'},
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window'}


wizard()
