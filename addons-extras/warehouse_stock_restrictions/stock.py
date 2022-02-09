# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from lxml import etree
from datetime import datetime


class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_locations = fields.Boolean('Restringir ubicaciones', default=True)

    stock_location_ids = fields.Many2many(
        'stock.location',
        'location_security_stock_location_users',
        'user_id',
        'location_id',
        'Stock Locations')

    stock_location_stock_ids = fields.Many2many(
        'stock.location',
        'location_stock_users',
        'user_id',
        'location_id',
        'Stock Locations')

    default_picking_type_ids = fields.Many2many(
        'stock.picking.type', 'stock_picking_type_users_rel',
        'user_id', 'picking_type_id', string='Operaciones Predeterminadas en Almacenes')


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
                user = self.env["res.users"].search(
                    [("id", "=", self.env.uid)])[0]
                #
                orig_ids = []
                for location in user.stock_location_stock_ids:
                    if location.usage not in ('supplier', 'production'):
                        orig_ids.append(location.id)

                # ids = [location.id for location in user.stock_location_stock_ids]

                # orig_ids = ids[:]  # list.copy se agregó en python 3.3


                if self.location_id.id in orig_ids:
                    orig_ids.remove(self.location_id.id)
                node.set('domain', "[('id', 'in', orig_ids)]")
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange("location_id")
    def onchange_new_location_id(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        location_ids = [location.id for location in user.stock_location_stock_ids]

        return {
            "domain": {
                "location_id": [("id", "in", location_ids)]
            }
        }

    @api.multi
    def write(self, values):
        if 'state' in values and values['state'] == 'confirm':
            values['confirmado_por'] = self._uid
            values['fecha_confirmacion'] = datetime.now().date()
        if 'state' in values and values['state'] == 'done':
            values['validado_por'] = self._uid
            values['fecha_validacion'] = datetime.now().date()
        vals = {}
        vals['fecha_modificacion'] = datetime.now().date()
        vals['modificado_por'] = self._uid
        vals['stock_inventory_id'] = self.id
        self.env['stock.inventory.modification.history'].create(vals)
        return super(stock_inventory, self).write(values)

    create_date = fields.Date(u'Fecha de creación', readonly=True)
    create_uid = fields.Many2one(
        comodel_name='res.users', string="Creado por", readonly=True)
    confirmado_por = fields.Many2one(
        comodel_name='res.users', string="Confirmado por", readonly=True)
    fecha_confirmacion = fields.Date(
        string=u"Fecha de confirmación", readonly=True)
    validado_por = fields.Many2one(
        comodel_name='res.users', string="Validado por", readonly=True)
    fecha_validacion = fields.Date(
        string=u"Fecha de validación", readonly=True)
    write_uid = fields.Many2one(
        comodel_name='res.users', string="Modificado por", readonly=True)
    write_date = fields.Date(u'Fecha de última modificación', readonly=True)
    inv_por_contabilidad = fields.Boolean('Inventario General')
    lineas_historial_modificaciones = fields.One2many(
        'stock.inventory.modification.history', 'stock_inventory_id', string='Lineas de historial de modificaciones')


class stock_inventory_modification_history(models.Model):
    _name = 'stock.inventory.modification.history'

    stock_inventory_id = fields.Many2one(
        'stock.inventory', string='Ajuste de inventario')
    fecha_modificacion = fields.Date(u'Fecha de modificación')
    modificado_por = fields.Many2one('res.users', string='Modificado por')


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
                user = self.env["res.users"].search(
                    [("id", "=", self.env.uid)])[0]
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
            locations = self.env["stock.location"].search(
                [("parent_left", "=", dest.parent_left)])
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
