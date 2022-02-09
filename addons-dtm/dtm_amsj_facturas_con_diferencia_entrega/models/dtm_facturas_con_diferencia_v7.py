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


class dtm_facturas_con_diferencia_en_entrega(osv.osv):
    _name = 'facturas.diferencia.entrega'
    _auto = False
    _order = 'date_invoice asc'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Proveedor', required=True),
        'purchase_order': fields.many2one('purchase.order', 'Pedido de Compra', required=True),
        'supplier_invoice_number': fields.char(string='Nro. de Factura del proveedor'),
        'origin': fields.char(string=u'Número de recepción'),
        'date_invoice': fields.date(string='Fecha de factura'),
        'picking_id': fields.many2one('stock.picking', 'Remito', required=True),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'facturas_diferencia_entrega')
        cr.execute("""
            CREATE OR REPLACE VIEW facturas_diferencia_entrega AS (
                SELECT distinct MIN(ai.id) as id,
                    ai.partner_id,
                    ai.supplier_invoice_number,
                    ai.origin,
                    ai.date_invoice,
                    sp.id as picking_id,
                    po.id as purchase_order
                FROM account_invoice ai
                    inner join account_invoice_line ail
                        on ail.invoice_id = ai.id and not lower(ail.name) like '%redondeo%'
                    inner join stock_picking sp
                        on sp.name = ai.origin
                    inner join purchase_order po
                        on po.name = sp.origin
                    left join(
                        select sp.name, sm.product_id, sm.product_qty
                        from stock_picking sp
                        inner join stock_move sm
                            on sm.picking_id = sp.id
                            where sp.state = 'done') as t
                        on t.name = ai.origin and ail.product_id = t.product_id and ail.quantity = t.product_qty
                        where
                            not ai.origin is null and t.name is null
                GROUP BY ai.partner_id, ai.supplier_invoice_number, ai.origin, ai.date_invoice, picking_id, purchase_order
        )""")


dtm_facturas_con_diferencia_en_entrega()
