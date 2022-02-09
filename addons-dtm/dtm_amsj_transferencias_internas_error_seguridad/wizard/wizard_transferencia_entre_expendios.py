# -*- coding: utf-8 -*-

from openerp import models, fields, api


class wizline3(models.TransientModel):
    _inherit = "wizard.transferencia.interna.line"
    _name = "wizard.transferencia.expendios.line"

    transf_id = fields.Many2one('wizard.transferencia.expendios')


class wizard(models.TransientModel):
    _inherit = "wizard.transferencia.interna"
    _name = "wizard.transferencia.expendios"

    move_lines = fields.One2many('wizard.transferencia.expendios.line')

    @api.multi
    def get_domain_expendio_dest(self):
        orig_ids = []
        user = self.env["res.users"].browse([self.env.uid])
        for default_picking_type in user.default_picking_type_ids:
            if default_picking_type.code == 'incoming':
                orig_ids.append(default_picking_type.default_location_dest_id.id)

        return [('id', '=', orig_ids)]

    # orig_ids = [location.id for location in
    #             self.env["stock.location"].search([("principal_del_expendio", "=", True)])
    #             ]
    #
    # user = self.env["res.users"].browse([self.env.uid])
    # for default_picking_type in user.default_picking_type_ids:  # Debería ser uno solo
    #     if default_picking_type.default_location_dest_id.id:
    #         dest = default_picking_type.default_location_dest_id
    #
    #         if dest.parent_left and dest.parent_left in orig_ids:
    #             orig_ids.remove(dest.parent_left)
    #
    # return [('id', '=', orig_ids)]

    @api.multi
    def get_domain_expendio_orig(self):
        ids = []
        obj_location = self.env['stock.location'].search([('usage', '=', 'internal')])
        for location in obj_location:
            if location.principal_del_expendio:
                # if not location.sector:
                    ids.append(location.id)

        return [('id', '=', ids)]

    expendios_location_orig_id = fields.Many2one('stock.location', domain=get_domain_expendio_orig)

    #  Entregar a , mis ubicaciones de entrada
    expendios_location_dest_id = fields.Many2one('stock.location', domain=get_domain_expendio_dest)

    # @api.onchange("new_location_orig_id")
    # def onchange_new_location_orig_id(self):
    #     orig_ids = [location.id \
    #         for location in self.env["stock.location"].search([("principal_del_expendio", "=", True)])
    #     ]
    #
    #     user = self.env["res.users"].browse([self.env.uid])
    #     for default_picking_type in user.default_picking_type_ids:  # Debería ser uno solo
    #         if default_picking_type.default_location_dest_id.id:
    #             dest = default_picking_type.default_location_dest_id
    #
    #             if dest.parent_left and dest.parent_left in orig_ids:
    #                 orig_ids.remove(dest.parent_left)
    #
    #     return {
    #         "domain": {
    #             "new_location_orig_id": [("id", "in", orig_ids)],
    #         }
    #     }
