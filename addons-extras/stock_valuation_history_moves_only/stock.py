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

class stock_history(osv.osv):
    _inherit = "stock.history"

    _columns = {
        'inventory_value': fields.float(string="Inventory Value", readonly=True),
    }

    def _get_inventory_value(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        # date = context.get('history_date')
        # product_tmpl_obj = self.pool.get("product.template")
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.quantity * line.price_unit_on_quant
        return res

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(osv.osv, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        return res

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                price_unit_on_quant,
                inventory_value,
                source
                FROM
                ((SELECT
                    stock_move.id::text AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    stock_move.product_qty AS quantity,
                    stock_move.date AS date,
                    product_product.cost_price AS price_unit_on_quant,
                    stock_move.product_qty*product_product.cost_price AS inventory_value,
                    stock_move.origin AS source
                FROM
                    stock_move
                LEFT JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                LEFT JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                LEFT JOIN
                    product_product ON product_product.id = stock_move.product_id
                LEFT JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE stock_move.state = 'done' AND dest_location.usage in ('internal')
                ) UNION
                (SELECT
                    '-' || stock_move.id::text AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - stock_move.product_qty AS quantity,
                    stock_move.date AS date,
                    product_product.cost_price AS price_unit_on_quant,
                    - stock_move.product_qty*product_product.cost_price AS inventory_value,
                    stock_move.origin AS source
                FROM
                    stock_move
                LEFT JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                LEFT JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                LEFT JOIN
                    product_product ON product_product.id = stock_move.product_id
                LEFT JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE stock_move.state = 'done' AND source_location.usage in ('internal')
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_categ_id, date, price_unit_on_quant, inventory_value, source
            )""")
