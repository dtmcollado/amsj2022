# -*- coding: utf-8 -*-
from datetime import datetime, date

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

CREATE = lambda values: (0, False, values)
UPDATE = lambda id, values: (1, id, values)
DELETE = lambda id: (2, id, False)
FORGET = lambda id: (3, id, False)
LINK_TO = lambda id: (4, id, False)
DELETE_ALL = lambda: (5, False, False)
REPLACE_WITH = lambda ids: (6, False, ids)


class wizard(models.TransientModel):
    _name = "wizard.anula.consumo"

    @api.multi
    def get_domain_orig(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        con_sector = []

        for location in user.stock_location_ids:
            if (not location.sector.id) and (not location.scrap_location):
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
    sector_ids = fields.Many2one('categoria', string="Sector")
    # move_ids = fields.One2many('stock.move', string='Moves')
    move_lines = fields.One2many('stock.move', inverse_name='id',
                                 String='Internal Moves')

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


            # @api.onchange("new_location_dest_id")
            # def cargo(self):

            # for product_id, cantidad_stock in self.env.cr.fetchall():
            #     # for item in stock_quants:  'product_uom': item.product_id.uom_id.id,
            #     lineas.create(
            #         {
            #             'product_id': product_id,
            #             'product_qty': 0,
            #             'product_uom_qty': 0,
            #             'stock': cantidad_stock,
            #             'transf_id': self.id
            #         }
            #     )
            #     # 4
            #     self.write({'move_lines': [(4, x) for x in lineas]})

    @api.onchange("new_location_orig_id")
    def onchange_new_location_dest_id(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        con_sector = []

        for location in user.stock_location_ids:
            if location.scrap_location:
                con_sector.append(location.id)

        if len(con_sector) == 1 and self.new_location_dest_id.id == False:
            self.new_location_dest_id = con_sector[0]

    @api.model
    @api.one
    def saco_productos(self):
        self.move_lines = self.env['stock.move'].search([('state', '=', 'confirmed'), ('product_uom_qty', '!=', 0.0)],
                                                        limit=None, order='priority desc, date_expected asc')

        lineas = self.env['stock.move'].search([('state', '=', 'confirmed'), ('product_uom_qty', '!=', 0.0)],
                                               limit=None, order='priority desc, date_expected asc')

        self.write({'move_lines': lineas})

        # lineas = self.env["wizard.reg.consumos.line"]
        #
        # consulta = """
        #                     SELECT stock_quant.product_id,sum(qty) as cantidad
        #                     FROM stock_quant
        # 		INNER JOIN product_product p ON p.id = stock_quant.product_id
        #                 INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
        #
        #         """
        #
        # if self.sector_ids:
        #     consulta += """
        #                 INNER JOIN categoria ct ON ct.id = pt.categoria_id and ct.id in %(sector_ids)s
        #                    where stock_quant.location_id = %(location_id)s
        # 		            group by stock_quant.product_id"""
        # else:
        #     consulta += """
        #                 INNER JOIN categoria ct ON ct.id = pt.categoria_id
        #                                where stock_quant.location_id = %(location_id)s
        #             		            group by stock_quant.product_id"""
        #
        # self.env.cr.execute(
        #     consulta,
        #     {'location_id': self.new_location_orig_id.id,
        #      'sector_ids': tuple(self.sector_ids.ids)
        #      })
        #
        # for product_id, cantidad_stock in self.env.cr.fetchall():
        #     # for item in stock_quants:  'product_uom': item.product_id.uom_id.id,
        #     lineas.create(
        #         {
        #             'product_id': product_id,
        #             'product_qty': 0,
        #             'product_uom_qty': 0,
        #             'stock': cantidad_stock,
        #             'transf_id': self.id
        #         }
        #     )
        #     # 4
        #     self.write({'move_lines': [(4, x) for x in lineas]})

    @api.multi
    def action_lista_productos(self):

        for line in self.move_lines:
            line.unlink()

            continue

        self.saco_productos()
        value = {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.anula.consumo',
            'views': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
            'res_id': self.id,
        }
        return value

    @api.multi
    def action_create_consumo(self):
        #
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
                    "sticky": True,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": self.new_location_orig_id,
            'location_dest_id': self.new_location_dest_id.id,
            'picking_type_id': wharehouse.out_type_id.id,
            'state': 'draft',
        })

        # picking_out.message_post(body='Albarán creado')

        for line in self.move_lines:
            if line.product_qty > 0:
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

        if len(self.move_lines) == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Pedidos",
                    "text": "No se encontraron productos para generar pedido",
                    "sticky": True,
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


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def anula_sp(self):

        self.ensure_one()
                ############ agregado Pedro
        self.env.cr.execute(


            """
                select sm.id
                    from stock_picking sp
                    inner join stock_move sm on sm.picking_id = sp.id
                    where sm.product_id = %(product_id)s
                    and sm.location_dest_id = %(almacen)s
                    and sm.date > timestamp %(ffecha_i)s
                    and sm.state in ('draft','done','confirmed','assigned','waiting')
            """



            , {
                'almacen': self.location_id.id,
                'ffecha_i': self.date,
                'product_id':self.product_id.id
            }
        )

        result = self.env.cr.fetchall()

        if len(result) < 1:

            self.env.cr.execute(
                """
                        SELECT * FROM
                        sp_generar_devolucion(%(picking)s);
    
    
                    """
                , {
                    'picking': self.picking_id.id
                }
            )

            resultado = self.env.cr.fetchall()

            for tupla in resultado:
                if tupla[0]:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            "title": "Gasto reversado",
                            "text": "Se reverso el Gasto para el o los productos involucrados",
                            "sticky": True,
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            "title": "Aviso:",
                            "text": tupla[1],
                            "sticky": True,
                        }
                    }


        else:
            return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            "title": "Aviso:",
                            "text": 'El producto ya fue enviado NO se puede reversar',
                            "sticky": True,
                        }
                    }














StockMove()
