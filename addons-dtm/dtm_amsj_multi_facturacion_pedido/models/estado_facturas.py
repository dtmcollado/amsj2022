from openerp import models, fields, models, api


class estado_facturas(models.Model):
    _inherit = 'stock.picking'
    _description = 'Description'

    @api.multi
    @api.depends('invoice_state')
    def _facturas_pendientes(self):
        todo = {}
        cantidades_facturadas = dict()
        cantidades_pendientes = None
        key = None
        name = None
        facturas_ya_creadas = []
        for rec in self:
            key = rec.id
            name = rec.name
            for move in rec.move_lines:
                todo.setdefault(key, [])
                todo[key].append(move)
                cantidades_facturadas[move.product_id] = 0

            facturas_ya_creadas = self.env['account.invoice'].search(
                [('origin', '=', rec.name), ('state', '!=', 'draft'), ('state', '!=', 'cancel')])

            rec.pendientes_facturacion = False
            rec.invoice_state_mje = ""

            for factura_id in facturas_ya_creadas:

                for invoice_line in factura_id.invoice_line:
                    producto = invoice_line.product_id
                    if cantidades_facturadas.get(producto) >= 0:
                        cantidades_facturadas[producto] += invoice_line.quantity

            cantidades_pendientes = dict()
            for move in rec.move_lines:
                prod = move.product_id
                if (move.product_qty - cantidades_facturadas[prod]) < 0:
                    cantidades_pendientes[prod] = 0
                else:
                    cantidades_pendientes[prod] = move.product_qty - cantidades_facturadas[prod]

            for key, value in cantidades_pendientes.items():
                if value > 0:
                    # u'2binvoiced'   invoice_state
                    if rec.invoice_state == 'none':
                        rec.pendientes_facturacion = False
                        rec.write({'pendientes_facturacion': False})
                        rec.invoice_state_mje = u""
                    else:
                        if rec.picking_type_id.code == u'incoming':
                            rec.pendientes_facturacion = True
                            rec.write({'pendientes_facturacion': True})
                            rec.invoice_state_mje = u"Atencion: tiene Productos sin Facturar."
                        else:
                            rec.pendientes_facturacion = False
                            rec.write({'pendientes_facturacion': False})
                            rec.invoice_state_mje = u""

    @api.multi
    def pendiente_facturar(self, invoice_ids):
        todo = {}
        cantidades_facturadas = dict()
        cantidades_pendientes = None
        key = None
        name = None
        facturas_ya_creadas = []
        for rec in self:
            key = rec.id
            name = rec.name
            for move in rec.move_lines:
                # if move.state == 'done':
                    todo.setdefault(key, [])
                    todo[key].append(move)
                    cantidades_facturadas[move.product_id] = 0

            facturas_ya_creadas = self.env['account.invoice'].search(
                [('id', 'in', invoice_ids.ids), ('state', '!=', 'draft'), ('state', '!=', 'cancel')])

            rec.pendientes_facturacion = False
            rec.invoice_state_mje = ""

            for factura_id in facturas_ya_creadas:
                for invoice_line in factura_id.invoice_line:
                    producto = invoice_line.product_id
                    if cantidades_facturadas.get(producto) >= 0:
                        cantidades_facturadas[producto] += invoice_line.quantity

            cantidades_pendientes = dict()
            for move in rec.move_lines:
                # estado = move.state
                if move.state == 'done':
                    prod = move.product_id
                    if (move.product_qty - cantidades_facturadas[prod]) < 0:
                        cantidades_pendientes[prod] = 0
                    else:
                        try:
                            cantidades_pendientes[prod] = (move.product_qty - cantidades_facturadas[prod]) + \
                                                          cantidades_pendientes[prod]
                        except KeyError:
                            cantidades_pendientes[prod] = (move.product_qty - cantidades_facturadas[prod])

            return cantidades_pendientes
            # for key, value in cantidades_pendientes.items():
            #     if value > 0:
            #         # u'2binvoiced'   invoice_state
            #         if rec.invoice_state == 'none':
            #             rec.pendientes_facturacion = False
            #             rec.write({'pendientes_facturacion': False})
            #             rec.invoice_state_mje = u""
            #         else:
            #             if rec.picking_type_id.code == u'incoming':
            #                 rec.pendientes_facturacion = True
            #                 rec.write({'pendientes_facturacion': True})
            #                 rec.invoice_state_mje = u"Atencion: tiene Productos sin Facturar."
            #             else:
            #                 rec.pendientes_facturacion = False
            #                 rec.write({'pendientes_facturacion': False})
            #                 rec.invoice_state_mje = u""

    pendientes_facturacion = fields.Boolean(string='Facturas pendientes', default=False, store=True)
    invoice_state_mje = fields.Char(string='Notificacion', compute='_facturas_pendientes')
