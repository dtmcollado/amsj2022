# -*- coding: utf-8 -*-

from openerp import models, fields, api


class wizline3(models.TransientModel):
    _inherit = "wizard.transferencia.interna.line"
    _name = "wizard.reposicion.line"

    transf_id = fields.Many2one('wizard.reposicion')

    @api.onchange("generico_id")
    def onchange_generico_id(self):
        self.product_id = False
        productos_no_incluir = []
        productos=[]
        product_ids = self.env['product.product'].search([('categoria_id','=',self.transf_id.expendios_location_orig_id.sector.id),('purchase_ok','=',True)])
        almacen_id = self.env['stock.warehouse'].browse(self.transf_id.expendios_location_dest_id.almacen_id.id)

        for stock in almacen_id.lot_stock_id.stock_critico:
            if stock.stock_critico == 0:
                productos_no_incluir.append(stock.product_tmpl_id.id)

        for producto in product_ids:
            if self.generico_id.id:
                if producto.principio_activo_id.id == self.generico_id.id and producto.id not in productos and producto.id not in productos_no_incluir:
                    productos.append(producto.id)
            else:
                if producto.id not in productos and producto.id not in productos_no_incluir:
                    productos.append(producto.id)

        return {'domain':{'product_id': [('id', 'in' ,productos)]}}




class wizard(models.TransientModel):
    _inherit = "wizard.transferencia.interna"
    _name = "wizard.reposicion"

    move_lines = fields.One2many('wizard.reposicion.line')

    @api.multi
    def get_domain_expendio_dest(self):
        orig_ids = []
        user = self.env["res.users"].browse([self.env.uid])
        for default_picking_type in user.default_picking_type_ids:
            if default_picking_type.code == 'incoming':
                orig_ids.append(default_picking_type.default_location_dest_id.id)

        return [('id', '=', orig_ids)]



    @api.multi
    def get_domain_expendio_orig(self):

        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        con_sector = []

        for location in user.stock_location_ids:
            if location.sector:
                con_sector.append(location.id)

        location_ids = con_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]

    expendios_location_orig_id = fields.Many2one('stock.location', domain=get_domain_expendio_orig)
    expendios_location_dest_id = fields.Many2one('stock.location', domain=get_domain_expendio_dest)

    @api.onchange("expendios_location_orig_id")
    def onchange_expendios_location_orig_id(self):
        self.move_lines =[]
