# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from lxml import etree

class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restringir ubicaciones', default=True)

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Operaciones Predeterminadas en Almacenes')

    sector_ids = fields.Many2many(comodel_name='categoria',
                                  string="Sectores"
                                  )

class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_inventory, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('type'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='location_id']"):

                ids = []
                user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
                ids = [location.id for location in user.stock_location_ids]

                orig_ids = ids[:]  # list.copy se agregó en python 3.3
                if self.location_id.id in orig_ids:
                    orig_ids.remove(self.location_id.id)
                node.set('domain', "[('id', 'in', orig_ids)]")
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange("location_id")
    def onchange_new_location_id(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        location_ids = [location.id for location in user.stock_location_ids]

        return {
            "domain": {
                "location_id": [("id", "in", location_ids)]
            }
        }



class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(stock_move, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('type'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='location_dest_id']"):

                    ids = []
                    user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
                    ids = [location.id for location in user.stock_location_ids]

                    orig_ids = ids[:]  # list.copy se agregó en python 3.3
                    if self.location_dest_id.id in orig_ids:
                        orig_ids.remove(self.location_dest_id.id)
                    node.set('domain', "[('id', 'in', orig_ids)]")
            res['arch'] = etree.tostring(doc)
        return res


    @api.one
    @api.constrains('state', 'location_id', 'location_dest_id')
    def check_user_location_rights(self):
        if self.state == 'draft':
            return True
        user_locations = self.env.user.stock_location_ids
        if self.env.user.restrict_locations:
            message = _(
                'Ubicación inválida. No puedes procesar esta transferencia '
                 'debido a que no controlas la ubicación "%s". '
                 'Por favor contacte a su Administrador.')
            if self.location_id not in user_locations:
                raise Warning(message % self.location_id.name)
            elif self.location_dest_id not in user_locations:
                raise Warning(message % self.location_dest_id.name)

    @api.onchange("location_id")
    def onchange_new_location_orig_id(self):
        user = self.env["res.users"].browse([self.env.uid])
        picking_type_ids = user.default_picking_type_ids

        location_ids = []

        for picking_type_id in picking_type_ids:
            dest = picking_type_id.default_location_dest_id
            locations = self.env["stock.location"].search([("parent_left", "=", dest.parent_left)])
            location_ids.extend([location.id for location in locations])

        return {
            "domain": {
                "location_id": [("id", "in", location_ids)]
            }
        }

    @api.onchange("location_dest_id")
    def onchange_new_location_dest_id(self):
        ids = []
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        ids = [location.id for location in user.stock_location_ids]

        orig_ids = ids[:]  # list.copy se agregó en python 3.3
        if self.location_dest_id.id in orig_ids:
            orig_ids.remove(self.location_dest_id.id)

        return {
            "domain": {
                "location_dest_id": [("id", "in", orig_ids)],
            }
        }