# -*- encoding: utf-8 -*-
from openerp import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime


class wizard(models.TransientModel):
    _name = "wizard.pedido.mensual"

    @api.multi
    def action_create_picking(self):
        lineas = []

        self._cr.execute("""       
                  SELECT rp.id as partner_id,product_id, sum(product_uom_qty) as quantity, product_uom  
                  FROM stock_move
                            INNER JOIN product_product p ON p.id = stock_move.product_id
                            INNER JOIN product_template pt ON pt.id = p.product_tmpl_id 
                            INNER JOIN stock_location l ON l.id = stock_move.location_id
                            LEFT JOIN product_supplierinfo psi ON psi.product_tmpl_id = pt.id
        	   	            LEFT JOIN res_partner rp ON rp.id = psi.name
                            INNER JOIN stock_picking_type pick on pick.id = stock_move.picking_type_id                    
                             where pt.categoria_id = 19 and stock_move.state = 'done' AND pick.code <> 'incoming'
                            group by rp.id, product_id , product_uom
                            """)

        lineas_ordenadas = self._cr.dictfetchall()

        user = self.env['res.users'].browse(self._uid)
        cocemi_ID = user.company_id.cocemi_id

        for line in lineas_ordenadas:
            product_id = self.env['product.product'].search([('id', '=', line['product_id'])], limit=1)

            date_planificada = datetime.today() + relativedelta(days=10 if line['partner_id'] else 0)

            line_dict = {}

            line_dict['name'] = product_id.name
            line_dict['price_unit'] = 1
            line_dict['date_planned'] = date_planificada
            line_dict['product_id'] = product_id.id
            line_dict['product_qty'] = line['quantity']
            line_dict['partner_id'] = line['partner_id']
            # line_dict['laboratorio_id'] = line['laboratorio_id']
            line_dict['state'] = 'draft'

            if line['partner_id']:
                lineas.append(line_dict)

        # self.origin = self.env['ir.sequence'].next_by_code('sec.nro.importacion_mensual')

        salida_ordenada = lineas

        primer_registro = True
        proveedor_aux = 0
        laboratorio_aux = 0
        es_cocemi = False

        orden = False
        for registro in salida_ordenada:
            if primer_registro:
                primer_registro = False
                proveedor_aux = registro.get('partner_id')
                proveedor_id = self.env['res.partner'].search([('id', '=', proveedor_aux)])
                # laboratorio_aux = registro.get('laboratorio_id')

                if proveedor_id.id == cocemi_ID.id:
                    es_cocemi = True
                else:
                    es_cocemi = False

                oc = {
                    'state': 'draft',
                    'shipped': False,
                    'partner_id': proveedor_id.id,
                    'location_id': proveedor_id.property_stock_supplier.id,
                    'date_order': datetime.today(),
                    'es_cocemi': es_cocemi,
                    'origin': 'Compra Mensual',
                    'pricelist_id': proveedor_id.property_product_pricelist.id or 1,
                    'currency_id': proveedor_id.property_product_pricelist.currency_id.id or 1
                    # 'laboratorio_id': registro.get('laboratorio_id'),


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
                if registro.get('partner_id') == proveedor_aux and registro.get('laboratorio_id') == laboratorio_aux:
                    registro['order_id'] = orden.id

                    order_line = self.env['purchase.order.line'].create(registro)
                    order_line._compute_tax_id()
                else:
                    proveedor_aux = registro.get('partner_id')
                    proveedor_id = self.env['res.partner'].search([('id', '=', proveedor_aux)])
                    if proveedor_id.id == cocemi_ID.id:
                        es_cocemi = True
                    else:
                        es_cocemi = False

                    if not proveedor_id.property_product_pricelist:
                        continue

                        # return {
                        #     'type': 'ir.actions.client',
                        #     'tag': 'action_warn',
                        #     'name': 'Notificación',
                        #     'params': {
                        #         'title': 'Error: Proveedor No esta ACTIVO',
                        #         'text': proveedor_aux.name,
                        #         'sticky': True
                        #     }
                        # }
                    if proveedor_id:
                        oc = {
                            'state': 'draft',
                            'shipped': False,
                            'partner_id': proveedor_id.id,
                            'location_id': proveedor_id.property_stock_supplier.id,
                            'date_order': datetime.today(),
                            'es_cocemi': es_cocemi,
                            'pricelist_id': proveedor_id.property_product_pricelist.id or 1,
                            'currency_id': proveedor_id.property_product_pricelist.currency_id.id or 1
                            }
                    else:
                        oc = False

                    #  se comenta codigo para que no genere la factura
                    #
                    if orden:
                        orden.action_picking_create()
                    #     orden.invoice_done()
                    # orden.action_invoice_create()
                    orden = False

                if oc:
                    orden = self.env['purchase.order'].create(oc)
                    registro['order_id'] = orden.id

                envio = orden.picking_type_id

                if envio.default_location_dest_id:
                    orden.location_id = envio.default_location_dest_id.id
                    orden.related_usage = envio.default_location_dest_id.usage
                    orden.related_location_id = envio.default_location_dest_id.id

                order_line = self.env['purchase.order.line'].create(registro)
                order_line._compute_tax_id()

                if orden:
                    orden.action_picking_create()





wizard()
