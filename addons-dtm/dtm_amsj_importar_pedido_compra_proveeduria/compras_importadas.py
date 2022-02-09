# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Datamatic All Rights Reserved.
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

from openerp import models, fields, api
from openerp.exceptions import Warning
from dateutil.relativedelta import relativedelta
from datetime import datetime

from dateutil.relativedelta import relativedelta

from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class dtm_amsj_compras_importadas_proveeduria(models.Model):
    _name = 'dtm.amsj.compras.importadas.proveeduria'
    _order = "date desc, name desc, id desc"

    name = fields.Char(string=u'Referencia/Descripción', index=True)

    date = fields.Date(string='Fecha',
                       index=True, copy=False)

    origin = fields.Char(string='Secuencia de importación', index=True, readonly=True)

    line_ids = fields.One2many('dtm.amsj.compras.importadas.lineas.proveeduria',
                               'importado_id', string='Lineas CSV')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('generada', u'Órdenes generadas')
    ],
        string='Estado', index=True, readonly=True,
        default='draft', copy=False)



    '''
    def _get_purchase_order_date(self, schedule_date):
        """Return the datetime value to use as Order Date (``date_order``) for the
           Purchase Order created to satisfy the given procurement. """
        self.ensure_one()
        seller_delay = int(self.product_id._select_seller(quantity=self.product_qty, uom_id=self.product_uom).delay)
        return schedule_date - relativedelta(days=seller_delay)

    def _get_purchase_schedule_date(self):
        """Return the datetime value to use as Schedule Date (``date_planned``) for the
           Purchase Order Lines created to satisfy the given procurement. """
        procurement_date_planned = datetime.strptime(self.date_planned, DEFAULT_SERVER_DATETIME_FORMAT)
        schedule_date = (procurement_date_planned - relativedelta(days=self.company_id.po_lead))
        return schedule_date
    '''



    @api.multi
    def purchase_confirm(self):
        account_fiscal_position = self.pool.get('account.fiscal.position')
        lineas = []
        for line in self.line_ids:
            if line.product_id and line.partner_id:

                date_planificada = datetime.today() + relativedelta(days=10 if line.partner_id else 0)

                taxes = line.product_id.supplier_taxes_id
                taxes_ids = account_fiscal_position.map_tax(self._cr,self._uid, False, taxes,self._context)

                # *****************************
                line_dict = {}
                # producto = line.product_id
                line_dict['name'] = line.product_id.name
                line_dict['price_unit'] = line.precio_unitario
                line_dict['taxes_id'] = taxes_ids
                line_dict['date_planned'] = date_planificada
                line_dict['product_id'] = line.product_id.id
                line_dict['product_qty'] = line.quantity
                line_dict['partner_id'] = line.partner_id.id
                line_dict['state'] = 'draft'

                lineas.append(line_dict)

        self.origin = self.env['ir.sequence'].next_by_code('sec.nro.importacion_proveeduria')

        salida_ordenada = sorted(lineas, key=lambda user: user['partner_id'])



        primer_registro = True
        proveedor_aux = 0

        orden = False
        for registro in salida_ordenada:


            if primer_registro:
                primer_registro = False
                proveedor_aux = registro.get('partner_id')
                proveedor_id = self.env['res.partner'].search([('id', '=', proveedor_aux)])

                if not proveedor_id.codigoAMSJ:

                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            'title': 'Error Laboratorio falta codigo AMSJ',
                            'text': proveedor_id.display_name,
                            'sticky': False
                        }
                    }

                if not proveedor_id.codigoAMSJ[:3] == 'med' or proveedor_id.codigoAMSJ[:3] == 'com':
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            'title': 'Error Laboratorio',
                            'text': proveedor_id.display_name,
                            'sticky': True
                        }
                    }

                if not proveedor_id.active:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'action_warn',
                        'name': 'Notificación',
                        'params': {
                            'title': 'Error Laboratorio No esta ACTIVO',
                            'text': proveedor_id.display_name,
                            'sticky': True
                        }
                    }
                oc = {
                    'state': 'approved',
                    'shipped': False,
                    'partner_id': proveedor_id.id,
                    'location_id': proveedor_id.property_stock_supplier.id,
                    'date_order': datetime.today(),
                    'pricelist_id': proveedor_id.property_product_pricelist.id,
                    'currency_id': proveedor_id.property_product_pricelist.currency_id.id,
                    'origin': self.origin,
                }

                orden = self.env['purchase.order'].create(oc)

                envio = orden.picking_type_id

                if envio.default_location_dest_id:
                   orden.location_id = envio.default_location_dest_id.id
                   orden.related_usage = envio.default_location_dest_id.usage
                   orden.related_location_id = envio.default_location_dest_id.id


                registro['order_id'] = orden.id
                order_line = self.env['purchase.order.line'].create(registro)
                order_line._compute_tax_id()

            else:
                actual = registro.get('partner_id')
                if registro.get('partner_id') == proveedor_aux:
                    registro['order_id'] = orden.id
                    order_line = self.env['purchase.order.line'].create(registro)
                    order_line._compute_tax_id()

                else:
                    proveedor_aux = registro.get('partner_id')
                    proveedor_id = self.env['res.partner'].search([('id', '=', proveedor_aux)])

                    if not proveedor_id:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'action_warn',
                            'name': 'Notificación',
                            'params': {
                                'title': 'Producto en planilla con nro de proveedor erroneo : ' + proveedor_aux,
                                'text': line.product_id.display_name,
                                'sticky': True
                            }
                        }

                    if not proveedor_id.codigoAMSJ[:3] == 'med' or proveedor_id.codigoAMSJ[:3] == 'com':
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'action_warn',
                            'name': 'Notificación',
                            'params': {
                                'title': 'Error Laboratorio',
                                'text': proveedor_id.display_name,
                                'sticky': True
                            }
                        }

                    if not proveedor_id.active:
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'action_warn',
                            'name': 'Notificación',
                            'params': {
                                'title': 'Error Laboratorio No esta ACTIVO',
                                'text': proveedor_id.display_name,
                                'sticky': True
                            }
                        }


                    oc = {
                        'state': 'approved',
                        'shipped': False,
                        'partner_id': proveedor_id.id,
                        'location_id': proveedor_id.property_stock_supplier.id,
                        'date_order': datetime.today(),
                        'pricelist_id': proveedor_id.property_product_pricelist.id,
                        'currency_id': proveedor_id.property_product_pricelist.currency_id.id,
                        'origin': self.origin,
                    }

                    # se comenta codigo para que no genere la factura
                    #
                    if orden:
                        orden.action_picking_create()
                        orden.invoice_done()
                        # orden.wkf_confirm_order()
                        # orden.action_invoice_create()
                        orden = False

                    orden = self.env['purchase.order'].create(oc)
                    # print order_line.display_name
                    registro['order_id'] = orden.id

                    envio = orden.picking_type_id

                    if envio.default_location_dest_id:
                        orden.location_id = envio.default_location_dest_id.id
                        orden.related_usage = envio.default_location_dest_id.usage
                        orden.related_location_id = envio.default_location_dest_id.id

                    order_line = self.env['purchase.order.line'].create(registro)
                    order_line._compute_tax_id()

        if orden:
            # se comenta codigo para que no genere la factura
            orden.action_picking_create()
            orden.invoice_done()
            # orden.wkf_confirm_order()
            # orden.action_invoice_create()
            self.write({'state': 'generada'})
            # orden = False


class dtm_amsj_compras_importadas_lineas_proveeduria(models.Model):
    _name = 'dtm.amsj.compras.importadas.lineas.proveeduria'

    name = fields.Text(string='Description', required=True )
    importado_id = fields.Many2one('dtm.amsj.compras.importadas.proveeduria', string='Referencia Compra Importada',
                                   ondelete='cascade', index=True)

    product_id = fields.Many2one('product.product', string='Producto',
                                 ondelete='restrict', index=True)
    quantity = fields.Integer(string='Cantidad', required=True, default=1)

    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True, store=True,
                                 index=True, compute="get_proveedor")

    precio_unitario = fields.Float(string='Precio Unitario', required=True, default=0)

    @api.one
    def get_proveedor(self):
        if self.product_id and self.product_id.seller_ids:
            self.partner_id = self.product_id.seller_ids.name.id
