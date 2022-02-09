# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Grzegorz Marczyński
#    Copyright 2016 QAQA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import models, api


class product_template(osv.osv):
    _inherit = 'product.template'

    def _cost_price(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}

        for id in ids:
            res[id] = {
                'cost_price': "Only for product variants",
                'has_bom': False,
            }
        return res

    _columns = {
        'cost_price': fields.function(_cost_price, type="char", string="Calculated cost price",multi='cost_price', readonly=True),
        'has_bom': fields.function(_cost_price, type="boolean", string="Manufactured here?", multi='cost_price',readonly=True),
    }

    @api.multi
    def recompute_cost_prices(self):
        self.pool.get('product.product').recompute_cost_prices(self._cr, self._uid, self._ids)

class product_product(osv.osv):
    _inherit = "product.product"

    def _has_bom(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}

        for id in ids:
            res[id] = False
            query = """SELECT b.id
                    FROM mrp_bom as b
                    WHERE b.product_id = %d AND b.active = TRUE
                """ % id
            cr.execute(query)
            for res_line in cr.fetchall():
                res[id] = True
                break

        return res

    _columns = {
        'cost_price': fields.float(string="Calculated cost price", readonly=True),
        'has_bom': fields.function(_has_bom, type="boolean", string="Manufactured here?", readonly=True),
    }

    @api.multi
    def recompute_cost_prices(self):
        # check if product is used in productions
        # if so, recalculate cost prices of all products above
        cr = self._cr
        uid = self._uid
        bom_needs = {}
        ids_set = set()
        new_ids = set([x.id for x in self.search([])])
        # for product in self:
        #     new_ids.add(product.id)

        to_new_ids = set()
        # add all products depending on producs from ids
        # we need to calculate all tree at once
        while len(new_ids) > 0:
            for id in new_ids:
                if not id in ids_set:
                    ids_set.add(id)
                    query = """SELECT bl.product_id, sum(bl.product_qty), b.id
                            FROM mrp_bom as b INNER JOIN mrp_bom_line as bl ON b.id= bl.bom_id
                            WHERE b.product_id = %d AND b.active = TRUE
                            GROUP BY bl.product_id, b.id
                            ORDER BY bl.product_id, b.id
                        """ % id
                    cr.execute(query)
                    bom_id = None
                    for res_line in cr.fetchall():
                        bom_product_id = res_line[0]
                        if bom_id and bom_id != res_line[2]:
                            break
                        bom_id = res_line[2]
                        if id not in bom_needs:
                            bom_needs[id] = []
                        bom_needs[id].append([bom_product_id,res_line[1],res_line[2]])
                        if not bom_product_id in ids_set and not bom_product_id in new_ids:
                            to_new_ids.add(bom_product_id)
            new_ids = to_new_ids
            to_new_ids = set()

        res = {}
        # recursevily update cost_price starting from products that do not depend on anything
        invalid_ids = ids_set
        valid_ids = set()
        while len(invalid_ids) > 0:
            for id in invalid_ids:
                valid = True
                bom_id = None
                bom_product_id = None
                if id not in bom_needs:
                    res[id] = {'cost_price' : self.browse(id).cost_price}
                else:
                    res[id] = {'cost_price' : 0}
                    for res_line in bom_needs[id]:
                        bom_product_id_old = bom_product_id
                        bom_product_id = res_line[0]
                        bom_id_old = bom_id
                        bom_id = res_line[2]
                        if bom_product_id_old == bom_product_id and bom_id_old <> bom_id:
                            # only one BOM per product
                            bom_id = None
                            continue
                        if bom_product_id in valid_ids:
                            res[id]['cost_price'] += res[bom_product_id]['cost_price'] * res_line[1]
                        else:
                            valid = False
                            break
                if valid:
                    valid_ids.add(id)
            invalid_ids = invalid_ids.difference(valid_ids)

        for id in res:
            self.pool.get('product.product').browse(cr,uid, id).update(res[id])

class Wizard(models.TransientModel):
    _name = 'product_cost_price.wizard'

    def _default_products(self):
        products = self.env['product.product'].browse(self._context.get('active_ids'))
        return [product.id for product in products]

    _columns = {
        'product_ids' :  fields.many2many('product.product', string="Product Variants", default=_default_products),
        'cost_price' : fields.float(string="Cost price", default=0.0),
    }

    @api.multi
    def set_cost_price(self):
        for product in self.product_ids:
            product.cost_price = self.cost_price

        return {}

