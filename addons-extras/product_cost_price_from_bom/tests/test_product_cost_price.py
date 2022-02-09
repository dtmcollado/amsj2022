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
from openerp.tests import common

@common.at_install(True)
@common.post_install(False)
class TestProduct(common.TransactionCase):
    def test_recompute_cost_prices(self):
        # first product - no bom
        product_template = self.env['product.template'].create({'name': 'Test Product Template'})
        product_variant = self.env['product.product'].create({'name': 'Test Product Variant','product_tmpl_id' : product_template.id})
        self.assertEqual(product_variant.product_tmpl_id.id, product_template.id)

        # set its cost price
        product_variant.cost_price = 1.5
        self.assertEqual(product_variant.cost_price, 1.5)
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant.cost_price, 1.5)

        # add empty bom
        product_variant_bom = self.env['mrp.bom'].create({'name': 'Bom Test Product Variant','product_tmpl_id' : product_template.id, 'product_id' : product_variant.id})
        self.assertEqual(product_variant_bom.product_tmpl_id.id, product_template.id)
        self.assertEqual(product_variant_bom.product_id.id, product_variant.id)

        # set product cost price
        product_variant.cost_price = 1.0
        self.assertEqual(product_variant.cost_price, 1.0)
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant.cost_price, 1.0)

        # add bom with one product
        product_template2 = self.env['product.template'].create({'name': 'Test Product Template2'})
        product_variant2 = self.env['product.product'].create({'name': 'Test Product Variant2','product_tmpl_id' : product_template2.id})
        self.assertEqual(product_variant2.product_tmpl_id.id, product_template2.id)
        product_variant_bom_line = self.env['mrp.bom.line'].create({'bom_id' : product_variant_bom.id, 'product_id': product_variant2.id})
        self.assertEqual(product_variant_bom_line.product_qty, 1.0)
        product_variant2.cost_price = 2.0
        self.assertEqual(product_variant2.cost_price, 2.0)
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant.cost_price, 2.0)

        # add second product to bom
        product_variant2a = self.env['product.product'].create(
            {'name': 'Test Product Variant2a', 'product_tmpl_id': product_template2.id})
        self.assertEqual(product_variant2a.product_tmpl_id.id, product_template2.id)
        product_variant_bom_line2 = self.env['mrp.bom.line'].create(
            {'bom_id': product_variant_bom.id, 'product_id': product_variant2a.id})
        self.assertEqual(product_variant_bom_line2.product_qty, 1.0)
        product_variant2a.cost_price = 5.0
        self.assertEqual(product_variant2a.cost_price, 5.0)
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant.cost_price, 2.0+5.0)

        # chenge quantity of products in bom
        product_variant_bom_line.product_qty = 2
        product_variant_bom_line2.product_qty = 3
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant.cost_price, 2*2+3*5)

        # add bom to second product with one product
        product_variant_bom2 = self.env['mrp.bom'].create({'name': 'Bom Test Product Variant','product_tmpl_id' : product_template2.id, 'product_id' : product_variant2.id})
        self.assertEqual(product_variant_bom2.product_tmpl_id.id, product_template2.id)
        self.assertEqual(product_variant_bom2.product_id.id, product_variant2.id)
        product_variant_bom_line3 = self.env['mrp.bom.line'].create({'bom_id' : product_variant_bom2.id, 'product_id': product_variant2a.id})
        self.assertEqual(product_variant_bom_line3.product_qty, 1.0)

        # update cost prices
        product_variant.recompute_cost_prices()
        self.assertEqual(product_variant2a.cost_price, 5)  #directly set cost price
        self.assertEqual(product_variant2.cost_price, 1*5) # new cost price from bom
        self.assertEqual(product_variant.cost_price, 2*5+3*5) # updated cost price from bom
