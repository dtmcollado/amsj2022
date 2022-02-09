# -*- encoding: utf-8 -*-

from datetime import date, timedelta, datetime
from openerp.exceptions import ValidationError
from openerp import models, fields, api, tools
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

CREATE = lambda values: (0, False, values)
UPDATE = lambda id, values: (1, id, values)
DELETE = lambda id: (2, id, False)
FORGET = lambda id: (3, id, False)
LINK_TO = lambda id: (4, id, False)
DELETE_ALL = lambda: (5, False, False)
REPLACE_WITH = lambda ids: (6, False, ids)


class wizline(models.TransientModel):
    _name = "wizard.pedido.consumo.interno.line"

    product_id = fields.Many2one('product.product', 'Product', required=True, select=True)
    product_qty = fields.Float('Quantity', help='Quantity in the default UoM of the product')
    transf_id = fields.Many2one('wizard.pedido.consumo.interno')


class wizard(models.TransientModel):
    _name = "wizard.pedido.consumo.interno"

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
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        sin_sector = []

        for location in user.stock_location_ids:
            if not location.sector.id:
                if location.usage == 'internal':
                    sin_sector.append(location.id)

        location_ids = sin_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]

    def _default_sector(self):
        return 17

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    fecha_inicial = fields.Datetime('Begin date')
    fecha_final = fields.Datetime('End date')

    inicial = fields.Datetime('fecha inicial', related='fecha_inicial', readonly=True)
    final = fields.Datetime('fecha inicial', related='fecha_final', readonly=True)

    sector_ids = fields.Many2one('categoria', string="Sector", default=_default_sector)

    move_lines = fields.One2many('wizard.pedido.consumo.interno.line', inverse_name='transf_id',
                                 String='Internal Moves', copy=True)

    cantidad = fields.Integer('cantidad')
    log = fields.Html('No encontrados')

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial >= self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    @api.one
    @api.onchange("new_location_dest_id")
    def onchange_location_id(self):

        if self.new_location_dest_id.fecha_ultima_reposicion:
            #  datetime.strptime(date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
            start_date = datetime.strptime(str(self.new_location_dest_id.fecha_ultima_reposicion), DEFAULT_SERVER_DATETIME_FORMAT)
            self.fecha_inicial = start_date
            end_date = datetime.strptime(str(datetime.today().replace(microsecond=0)), DEFAULT_SERVER_DATETIME_FORMAT)

            self.fecha_final = end_date
        else:
            start_date = datetime.today().replace(microsecond=0) - timedelta(days=7)
            start_date = start_date
            end_date = datetime.today().replace(microsecond=0)
            self.fecha_inicial = datetime.strptime(str(start_date), DEFAULT_SERVER_DATETIME_FORMAT)
            self.fecha_final = datetime.strptime(str(end_date), DEFAULT_SERVER_DATETIME_FORMAT)

    # def formato_fecha(self, fecha, dias_a_agregar=0):
    #     fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
    #     if dias_a_agregar:
    #         fecha = fecha + timedelta(days=dias_a_agregar)
    #         fecha2 = fecha.strftime('%d/%m/%Y %H:%M:%S')
    #     return fecha2

    @api.multi
    def action_lista_productos(self):




        # sector_id = self.sector_ids.id
        #
        # fecha_i = self.fecha_inicial
        # fecha_f = self.fecha_final

        # self.env.cr.execute(
        #
        #     """
        #              SELECT product_id, sum(product_uom_qty) as cantidad
        #         FROM stock_move
        #         INNER JOIN product_product p ON p.id = stock_move.product_id
        #         INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
        #         INNER JOIN stock_location sl ON sl.id = stock_move.location_dest_id
        #            where sl.almacen_id = %(almacen)s  AND
        #                  pt.categoria_id = %(sector)s AND
        #                  stock_move.location_id = %(location_dest_id)s
        #                  AND (date >= timestamp %(ffecha_i)s and
        #                     date <= timestamp %(ffecha_f)s)
        #         group by product_id
        #         ;
        #     """
        #
        #     , {
        #         'almacen': self.new_location_dest_id.almacen_id.id,
        #         'location_dest_id': self.new_location_dest_id.id,
        #         'sector': sector_id,
        #         'ffecha_i': fecha_i,
        #         'ffecha_f': fecha_f
        #     }
        # )



        self.env.cr.execute(
            """
                        SELECT distinct product_id,product_tmpl_id,uom_id,sum(qty) as cantidad 
                        FROM sp_reponer(%(location_id)s,%(location_stock_id)s,%(ffecha_i)s,%(ffecha_f)s)
                        GROUP BY product_id,product_tmpl_id,uom_id; 
                        ;

                    """
            , {
                'location_id': self.new_location_dest_id.id,
                'location_stock_id': self.new_location_dest_id.almacen_id.lot_stock_id.id,
                'ffecha_i': self.fecha_inicial,
                'ffecha_f': self.fecha_final
            }
        )

        # self.new_location_dest_id.almacen_id.lot_stock_id.id

        resultado = self.env.cr.fetchall()
        lineas = list()

        for tupla in resultado:
            if not tupla[0] == 0:
                producto_id = tupla[0]
                cantidad_a_reponer = tupla[3]

                nuevo = {
                    'product_id': producto_id,
                    'product_qty': cantidad_a_reponer,
                }

                linea = self.env['wizard.pedido.consumo.interno.line'].create(nuevo)
                lineas.append(linea)

        self.write({'move_lines': [(6, 0, [linea.id for linea in lineas])]})
        self.move_lines = [(6, 0, [linea.id for linea in lineas])]

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.pedido.consumo.interno',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_create_picking_interno(self):
        ubicacion_destino = self.new_location_dest_id
        almacen = ubicacion_destino.almacen_id
        ubicacion_origen = self.env['stock.location'].search([('almacen_id', '=', almacen.id),
                                                              ('principal_del_expendio', '=', True)], limit=1)

        if ubicacion_origen.id == ubicacion_destino.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": u"Origen y Destino deben de ser diferentes. Verifique la ubicación principal del almacén.",
                    "sticky": True,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": ubicacion_origen.id,
            'location_dest_id': ubicacion_destino.id,
            'picking_type_id': almacen.int_type_id.id,
            'sector_id': int(17),
        })

        for line in self.move_lines:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_out.id,
                'picking_type_id': ubicacion_destino.almacen_id.int_type_id.id,
                'location_id': ubicacion_origen.id,
                'location_dest_id': ubicacion_destino.id,
                'state': "confirmed",
            })

        if not self.move_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": "No se encontraron productos para generar transferencia.",
                    "sticky": True,
                }
            }
        else:
            # actualizo fecha ultima reposicion
            hoy = datetime.strptime(str(datetime.today().replace(microsecond=0)), DEFAULT_SERVER_DATETIME_FORMAT)
            ubicacion_destino.write({'fecha_ultima_reposicion': hoy})

            return {
                'domain': [('id', '=', picking_out.id)],
                'name': 'x Consumo Interno',
                'view_mode': 'tree,form',
                'view_type': 'form',
                'context': {'tree_view_ref': 'stock.picking.tree'},
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window'}


wizard()
