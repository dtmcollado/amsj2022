# coding: utf-8
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, _
from lxml import etree
import datetime,time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

class StockInventoryEmptyLines(models.Model):
    _name = 'stock.inventory.line.empty'

    product_code = fields.Char(
        string='Product Code', size=64, required=True)
    product_qty = fields.Float(
        string='Quantity', required=True, default=1.0)
    inventory_id = fields.Many2one(
        comodel_name='stock.inventory', string='Inventory',
        required=True, ondelete="cascade")


class StockInventoryFake(object):
    def __init__(self, inventory, product=None, lot=None):
        self.id = inventory.id
        self.location_id = inventory.location_id
        self.product_id = product
        self.lot_id = lot
        self.partner_id = inventory.partner_id
        self.package_id = inventory.package_id


class StockInventory(models.Model):
    _inherit = 'stock.inventory'


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockInventory, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        location_ids = []
        user = self.env["res.users"].browse(self._uid)
        for location in user.stock_location_ids:
            if location.usage not in ('supplier','production'):
                location_ids.append(location.id)

        domain_user2 = str([('id', 'in', location_ids)])

        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='location_id']"):
           node.set('domain',domain_user2)
           res['arch'] = etree.tostring(doc)
        return res



    @api.model
    def _get_available_filters(self):
        """This function will return the list of filters allowed according to
        the options checked in 'Settings/Warehouse'.

        :return: list of tuple
        """
        res_filters = super(StockInventory, self)._get_available_filters()
        res_filters.append(('categories', _('Familias de productos')))
        res_filters.append(('groups', _('Grupo de productos')))
        res_filters.append(('products', _('Productos seleccionados')))
        res_filters.append(('sectores', _('Sectores de productos')))
        res_filters.append(('tipos', _(u'Tipos de fármacos')))
        # Categoría Interna
        res_filters.append(('categoria_interna', _(u'Categoría Interna')))
        for res_filter in res_filters:
            if res_filter[0] == 'lot':
                res_filters.append(('lots', _('Lotes seleccionados')))
        res_filters.append(('empty', _('Empty list')))
        return res_filters

    filter = fields.Selection(
        selection=_get_available_filters, string='Selection Filter',
        required=True)
    categ_ids = fields.Many2many(
        comodel_name='familia', relation='rel_inventories_categories',
        column1='inventory_id', column2='familia_id', string='Familias de productos')
    tipo_ids = fields.Many2many(
        comodel_name='tipo', relation='rel_inventories_tipos',
        column1='inventory_id', column2='tipo_id', string='Tipo de productos')
    #
    categ_interna_ids = fields.Many2many(
        comodel_name='product.category', relation='rel_inventories_product_category',
        column1='inventory_id', column2='categ_id', string='Categoría Interna')
    #
    group_ids = fields.Many2many(
        comodel_name='grupo', relation='rel_inventories_grupos',
        column1='inventory_id', column2='familia_id', string='Grupos de productos')
    product_ids = fields.Many2many(
        comodel_name='product.product', relation='rel_inventories_products',
        column1='inventory_id', column2='product_id', string='Products')
    lot_ids = fields.Many2many(
        comodel_name='stock.production.lot', relation='rel_inventories_lots',
        column1='inventory_id', column2='lot_id', string='Lots')
    empty_line_ids = fields.One2many(
        comodel_name='stock.inventory.line.empty', inverse_name='inventory_id',
        string='Capture Lines')
    sector_ids = fields.Many2many(
        comodel_name='categoria', relation='rel_inventories_sectores_categ',
        column1='inventory_id', column2='categoria_id', string='Sector de productos')
    location_id = fields.Many2one(comodel_name='stock.location',string=u'Ubicación de inventario',copy=False,default=False,required=True)

    domain_product_ids = fields.Many2many(
        comodel_name='product.product', relation='rel_listado_productos',
        column1='product_id', column2='id', string='Listado de productos')


    def prepare_inventory(self, cr, uid, ids, context=None):
        inventory_line_obj = self.pool.get('stock.inventory.line')
        for inventory in self.browse(cr, uid, ids, context=context):
            # If there are inventory lines already (e.g. from import), respect those and set their theoretical qty
            line_ids = [line.id for line in inventory.line_ids]
            if not line_ids:
                    # and inventory.filter != 'partial':
                #compute the inventory lines and create them
                vals = self._get_inventory_lines(cr, uid, inventory, context=context)
                for product_line in vals:
                    if product_line['theoretical_qty']:
                        if product_line['theoretical_qty'] != 0:
                            inventory_line_obj.create(cr, uid, product_line, context=context)
        return self.write(cr, uid, ids, {'state': 'confirm', 'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})


    @api.model
    def _get_inventory_lines(self, inventory):
        vals = []
        products = False
        product_tmpl_obj = self.env['product.template']
        product_obj = self.env['product.product']
        if inventory.filter in ('categories', 'products','groups','sectores','tipos','categoria_interna','partial'):
            products = product_obj

            if inventory.filter == 'partial':
                product_tmpls = product_tmpl_obj.search(
                    [('active', '=', True)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])

            if inventory.filter == 'groups':
                product_tmpls = product_tmpl_obj.search(
                    [('grupo_id', 'in', inventory.group_ids.ids)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])
            if inventory.filter == 'categories':
                product_tmpls = product_tmpl_obj.search(
                    [('familia_id', 'in', inventory.categ_ids.ids)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])
            # categoria_interna
            if inventory.filter == 'categoria_interna':
                product_tmpls = product_tmpl_obj.search(
                    [('categ_id', 'in', inventory.categ_interna_ids.ids)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])
            # ********************
            if inventory.filter == 'sectores':
                product_tmpls = product_tmpl_obj.search(
                    [('categoria_id', 'in', inventory.sector_ids.ids)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])
            if inventory.filter == 'tipos':
                product_tmpls = product_tmpl_obj.search(
                    [('tipo_id', 'in', inventory.tipo_ids.ids)])
                products = product_obj.search(
                    [('product_tmpl_id', 'in', product_tmpls.ids)])
            elif inventory.filter == 'products':
                products = inventory.product_ids
            for product in products:
                fake_inventory = StockInventoryFake(inventory, product=product)
                vals += super(StockInventory, self)._get_inventory_lines(
                    fake_inventory)
        elif inventory.filter == 'lots':
            for lot in inventory.lot_ids:
                fake_inventory = StockInventoryFake(inventory, lot=lot)
                vals += super(StockInventory, self)._get_inventory_lines(
                    fake_inventory)
        elif inventory.filter == 'empty':
            tmp_lines = {}
            empty_line_obj = self.env['stock.inventory.line.empty']
            for line in inventory.empty_line_ids:
                if line.product_code in tmp_lines:
                    tmp_lines[line.product_code] += line.product_qty
                else:
                    tmp_lines[line.product_code] = line.product_qty
            inventory.empty_line_ids.unlink()
            for product_code in tmp_lines.keys():
                products = product_obj.search([
                    '|', ('default_code', '=', product_code),
                    ('ean13', '=', product_code),
                ])
                if products:
                    product = products[0]
                    fake_inventory = StockInventoryFake(
                        inventory, product=product)
                    values = super(StockInventory, self)._get_inventory_lines(
                        fake_inventory)
                    if values:
                        values[0]['product_qty'] = tmp_lines[product_code]
                    else:
                        empty_line_obj.create(
                            {
                                'product_code': product_code,
                                'product_qty': tmp_lines[product_code],
                                'inventory_id': inventory.id,
                            })
                    vals += values
        else:
            vals = super(StockInventory, self)._get_inventory_lines(
                inventory)
        if products:
            inventory.domain_product_ids = products.ids
        return vals


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'
    _order = 'product_name ASC'

    @api.multi
    def get_familia(self):
        for rec in self:
            rec.familia_id = False
            if rec.product_id:
                if rec.product_id.product_tmpl_id:
                    product_tmpl_id = self.env['product.template'].browse(rec.product_id.product_tmpl_id.id)
                    if product_tmpl_id.familia_id:
                        rec.familia_id = product_tmpl_id.familia_id.id

    @api.multi
    def get_principio_activo_id(self):
        for rec in self:
            rec.familia_id = False
            if rec.product_id:
                if rec.product_id.product_tmpl_id:
                    product_tmpl_id = self.env['product.template'].browse(rec.product_id.product_tmpl_id.id)
                    if product_tmpl_id.principio_activo_id:
                        rec.generico = product_tmpl_id.principio_activo_id.id

    @api.multi
    def get_presentacion(self):
        for rec in self:
            rec.familia_id = False
            if rec.product_id:
                if rec.product_id.product_tmpl_id:
                    product_tmpl_id = self.env['product.template'].browse(rec.product_id.product_tmpl_id.id)
                    if product_tmpl_id.presentacion_id:
                        rec.presentacion = str(product_tmpl_id.presentacion_valor) + ' ' + product_tmpl_id.presentacion_id.name
                    else:
                        rec.presentacion = str(product_tmpl_id.presentacion_valor)


    familia_id = fields.Many2one(comodel_name='familia', string='Familia', compute='get_familia', readonly=True)
    generico = fields.Many2one(comodel_name='principio.activo', string=u'Genérico', compute='get_principio_activo_id',
                               readonly=True)
    presentacion = fields.Char(string=u'Presentación', readonly=True,compute='get_presentacion')

    domain_product_ids = fields.Many2many(
        comodel_name='product.product', relation='rel_listado_productos_linea',
        column1='product_id', column2='id', string='Listado de productos')

StockInventoryLine()
