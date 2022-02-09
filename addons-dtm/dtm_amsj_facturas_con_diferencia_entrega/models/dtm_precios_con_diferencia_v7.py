# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Datamatic All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import tools
from openerp.osv import fields, osv


class dtm_precios_con_diferencia(osv.osv):
    _name = 'diferencia.precio.ordenes.facturas'
    _auto = False
    # _order = 'date_invoice DESC'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Proveedor', readonly=True),
        'purchase_order': fields.char('Pedido de Compra',  readonly=True),
        'supplier_invoice_number': fields.char(string='Nro. de Factura del proveedor', readonly=True),
        'date_invoice': fields.date(string='Fecha de factura', readonly=True),
        'date_order': fields.date(string='Fecha de orden de compra', readonly=True),
        'referencia_interna': fields.char(string=u"Código", readonly=True),
        'precio_factura': fields.float(string=u'Precio en Factura', readonly=True),
        'precio_orden': fields.float(string=u'Precio en Orden', readonly=True),
        'name': fields.char(string=u'Producto', readonly=True),
        'sector_id': fields.many2one('categoria', string="Sector" , readonly=True),
        'cantidad_factura': fields.float(digits=(32, 0), string='Cantidad Factura', readonly=True),
        'cantidad_orden':  fields.float(digits=(32, 0), string='Cantidad Orden', readonly=True),
        'categoria_interna': fields.char(string=u'Categoria Interna', readonly=True)
    #     categ_id

    }
#
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'diferencia_precio_ordenes_facturas')
        cr.execute("""
    CREATE OR REPLACE VIEW public.diferencia_precio_ordenes_facturas AS 

SELECT ail.id,
    po.id AS id_orden,
    ai.partner_id,
    rp.name AS proveedor,
    ai.supplier_invoice_number,
    po.sector_id,
    ai.date_invoice,
    po.name AS purchase_order,
    po.date_order,
    ail.product_id,
    pt.name,
    pp.default_code AS referencia_interna,
    ail.price_unit::numeric(16,2) AS precio_factura,
    pol.price_unit::numeric(16,2) AS precio_orden,
    ail.quantity AS cantidad_factura,
    pol.product_qty AS cantidad_orden,
    t.name AS categoria_interna
   FROM account_invoice ai
     JOIN account_invoice_line ail ON ail.invoice_id = ai.id AND NOT lower(ail.name) ~~ '%redondeo%'::text
     JOIN stock_picking sp ON sp.name::text = ai.origin::text
     JOIN purchase_order po ON po.name::text = sp.origin::text
     JOIN purchase_order_line pol ON pol.order_id = po.id AND pol.product_id = ail.product_id
     JOIN product_product pp ON pp.id = pol.product_id
     JOIN product_template pt ON pt.id = pp.product_tmpl_id
     JOIN res_partner rp ON rp.id = ai.partner_id
     JOIN product_category t ON t.id = pt.categ_id
  WHERE NOT ai.origin IS NULL AND pol.price_unit <> ail.price_unit;


ALTER TABLE public.diferencia_precio_ordenes_facturas
  OWNER TO odoo;

""")


dtm_precios_con_diferencia()
