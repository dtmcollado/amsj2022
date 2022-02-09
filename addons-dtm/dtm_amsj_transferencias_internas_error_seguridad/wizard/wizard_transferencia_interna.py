# -*- coding: utf-8 -*-

from openerp import models, fields, api


class wizline2(models.TransientModel):

    _inherit = "wizard.transferencia.interna.line"
    _name = "wizard.transferencia.interna.line2"

    transf_id = fields.Many2one('wizard.transferencia.interna2')


class wizard(models.TransientModel):

    _inherit = "wizard.transferencia.interna"

    # _name no puede ser "wizar.transferencia.interna" porque así
    # se llama el wizard de reposición, intenté renombrar el wizard
    # de reposición pero daba errores por todos lados
    _name = "wizard.transferencia.interna2"

    move_lines = fields.One2many('wizard.transferencia.interna.line2')



    @api.multi
    def get_domain_orig(self):
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        sin_sector = []

        for location in user.stock_location_ids:
            if not location.sector.id:
                if not location.scrap_location:
                    sin_sector.append(location.id)

        location_ids = sin_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]

    @api.multi
    def get_domain_dest(self):
        # user = self.env["res.users"].browse([self.env.uid])
        # location_ids = [loc.id for loc in user.stock_location_ids]
        # wharehouses = self.env['stock.warehouse'].search([
        #     ('wh_input_stock_loc_id', 'in', location_ids)
        # ])
        #
        # # if len(wharehouses) > 0:
        # #     wharehouse = wharehouses[0]
        # #     if self.new_location_dest_id.id == False:
        # #         self.new_location_dest_id = wharehouse.wh_input_stock_loc_id
        #
        # return [('id', 'in', [wh.wh_input_stock_loc_id.id for wh in wharehouses])]
        user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
        sin_sector = []

        for location in user.stock_location_ids:
            if not location.sector.id:
                # if not location.scrap_location:
                    sin_sector.append(location.id)

        location_ids = sin_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]
    # @api.onchange("new_location_orig_id")
    # def onchange_new_location_orig_id(self):
    #     user = self.env["res.users"].browse([self.env.uid])
    #     location_ids = [loc.id for loc in user.stock_location_ids]
    #     wharehouses = self.env['stock.warehouse'].search([
    #         ('wh_input_stock_loc_id', 'in', location_ids)
    #     ])
    #
    #     if len(wharehouses) > 0:
    #         wharehouse = wharehouses[0]
    #         if self.new_location_orig_id.id == False:
    #             self.new_location_orig_id = wharehouse.wh_input_stock_loc_id

    # @api.onchange("new_location_dest_id")
    # def onchange_new_location_dest_id(self):
    #     ids = []
    #     user = self.env["res.users"].search([("id", "=", self.env.uid)])[0]
    #     ids = [location.id for location in user.stock_location_ids]
    #
    #     orig_ids = ids[:]  # list.copy se agregó en python 3.3
    #     if self.new_location_dest_id.id in orig_ids:
    #         orig_ids.remove(self.new_location_dest_id.id)
    #
    #     return {
    #         "domain": {
    #             "new_location_orig_id": [("id", "in", orig_ids)],
    #         }
    #     }

    internal_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    internal_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)