# -*- coding: utf-8 -*-

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.exceptions import ValidationError

class stock_invoice_onshipping(osv.osv_memory):
    _name = "stock.invoice.onshipping"
    _inherit = "stock.invoice.onshipping"

    def view_init(self, cr, uid, fields_list, context=None):
        """
        La función sobreescribe al método de la clase que controla el estado
        de los albaranes pra determinar si se puede facturar y en su lugar
        no hace nada para evitar a la vez los controles y alterar los valores.

        A continuación se muestra el código original que es sobreescrito.

        if context is None:
            context = {}
        res = super(stock_invoice_onshipping, self).view_init(cr, uid, fields_list, context=context)
        pick_obj = self.pool.get('stock.picking')
        count = 0
        active_ids = context.get('active_ids',[])
        for pick in pick_obj.browse(cr, uid, active_ids, context=context):
            if pick.invoice_state != '2binvoiced':
                count += 1
        if len(active_ids) == count:
            raise osv.except_osv(_('Warning!'), _('None of these picking lists require invoicing.'))
        return res

        """
        pass


stock_invoice_onshipping()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='out_invoice', context=None):

        """
        Se sobreescribe este método para evitar los controles que impide volver
        a facturar. Queda librado al usuario.

        A continuación se muestra el código original que es sobreescrito.

        context = context or {}
        todo = {}
        for picking in self.browse(cr, uid, ids, context=context):
            partner = self._get_partner_to_invoice(cr, uid, picking, dict(context, type=type))
            #grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_lines:
                if move.invoice_state == '2binvoiced':
                    if (move.state != 'cancel') and not move.scrapped:
                        todo.setdefault(key, [])
                        todo[key].append(move)
        invoices = []
        for moves in todo.values():
            invoices += self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)
        return invoices

        """

        # order = self.env['purchase.order'].search([('name', '=', self.origin)])
        # sql = """
        #     SELECT m.product_id, m.price_unit, m.product_qty - t.quantity as pendiente
        #     FROM stock_move m
        #     INNER JOIN stock_picking sp ON sp.id = m.picking_id
        #     LEFT JOIN (
        #         SELECT ai.origin, ail.product_id, SUM(ail.quantity) AS quantity
        #         FROM account_invoice ai
        #         INNER JOIN account_invoice_line ail ON ai.id = ail.invoice_id
        #         GROUP BY ai.origin, ail.product_id
        #     ) AS t ON t.origin = sp.name AND m.product_id = t.product_id
        #     WHERE sp.name=%(name)s
        # """

        context = context or {}
        todo = {}
        invoice_obj = self.pool.get('account.invoice')

        ori = ""
        orig = 0
        pickings = self.browse(cr, uid, ids, context=context)

        # x = ', '.join(pickings.name)

        for picking in pickings:
            if ori == "":
                ori = picking.name
            else:
                ori = ori + ', ' + picking.name
            orig += 1

        for picking in pickings:
            partner = self._get_partner_to_invoice(cr, uid, picking, dict(context, type=type))
            # grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id

            cantidades_facturadas = dict()
            for move in picking.move_lines:
                todo.setdefault(key, [])
                todo[key].append(move)
                cantidades_facturadas[move.product_id] = 0

            # if orig > 1:
            #     facturas_ya_creadas = invoice_obj.search(cr, uid, [('origin', '=', ori)], context=context)
            # else:
            facturas_ya_creadas = invoice_obj.search(cr, uid, [('origin', '=', picking.name)], context=context)

            for factura_id in facturas_ya_creadas:
                factura = invoice_obj.browse(cr, uid, factura_id, context=context)
                for invoice_line in factura.invoice_line:
                    producto = invoice_line.product_id
                    if cantidades_facturadas.get(producto) >= 0:
                        cantidades_facturadas[producto] += invoice_line.quantity
                    # else:
                    #     raise ValidationError("No existen mas productos para facturar")

            cantidades_pendientes = dict()
            for move in picking.move_lines:
                prod = move.product_id
                if (move.product_qty - cantidades_facturadas[prod]) < 0:
                    cantidades_pendientes[prod] = 0
                else:
                    cantidades_pendientes[prod] = move.product_qty - cantidades_facturadas[prod]


        if len(facturas_ya_creadas) > 0:
            invoices = []
            invoice_line_obj = self.pool.get('account.invoice.line')
            for moves in todo.values():
                invoice_values = self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)

                invoices += invoice_values
            for invoice in invoices:
                line_ids = invoice_line_obj.search(cr, uid, [('invoice_id', '=', invoice)], context=context)
                for line_id in line_ids:
                    try:
                        line = invoice_line_obj.browse(cr, uid, line_id, context=context)
                        line.quantity = cantidades_pendientes[line.product_id]
                        if cantidades_pendientes[line.product_id] == 0:
                            invoice_line_obj.unlink(cr, uid, line_id, context=context)
                    except Exception:
                        pass
            return invoices
        else:
            invoices = []
            for moves in todo.values():
                invoices += self._invoice_create_line(cr, uid, moves, journal_id, type, context=context)
            return invoices

stock_picking()

class stock_invoice_onshipping(osv.osv_memory):
    _inherit = "stock.invoice.onshipping"
    # _description = "Stock Invoice Onshipping"
    # _columns = {
    #     'journal_id': fields.many2one('account.journal', 'Destination Journal', required=True),
    #     'journal_type': fields.selection([('purchase_refund', 'Refund Purchase'), ('purchase', 'Create Supplier Invoice'),
    #                                       ('sale_refund', 'Refund Sale'), ('sale', 'Create Customer Invoice')], 'Journal Type', readonly=True),
    #     'group': fields.boolean("Group by partner"),
    #     'invoice_date': fields.date('Invoice Date'),
    # }

    def create_invoice(self, cr, uid, ids, context=None):
        context = dict(context or {})
        picking_pool = self.pool.get('stock.picking')
        data = self.browse(cr, uid, ids[0], context=context)
        journal2type = {'sale':'out_invoice', 'purchase':'in_invoice', 'sale_refund':'out_refund', 'purchase_refund':'in_refund'}
        context['date_inv'] = data.invoice_date
        acc_journal = self.pool.get("account.journal")
        inv_type = journal2type.get(data.journal_id.type) or 'out_invoice'
        context['inv_type'] = inv_type

        active_ids = context.get('active_ids', [])
        res = picking_pool.action_invoice_create(cr, uid, active_ids,
              journal_id = data.journal_id.id,
              group = data.group,
              type = inv_type,
              context=context)
        return res

    def open_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        invoice_ids = self.create_invoice(cr, uid, ids, context=context)
        if not invoice_ids:
            raise osv.except_osv(_('Error!'), _('No invoice created!'))

        data = self.browse(cr, uid, ids[0], context=context)

        action_model = False
        action = {}

        journal2type = {'sale': 'out_invoice', 'purchase': 'in_invoice', 'sale_refund': 'out_refund',
                        'purchase_refund': 'in_refund'}
        inv_type = journal2type.get(data.journal_id.type) or 'out_invoice'
        data_pool = self.pool.get('ir.model.data')
        if inv_type == "out_invoice":
            action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree1')
        elif inv_type == "in_invoice":
            action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree2')
        elif inv_type == "out_refund":
            action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree3')
        elif inv_type == "in_refund":
            action_id = data_pool.xmlid_to_res_id(cr, uid, 'account.action_invoice_tree4')

        if action_id:
            action_pool = self.pool['ir.actions.act_window']
            action = action_pool.read(cr, uid, action_id, context=context)
            action['domain'] = "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
            return action
        return True


stock_invoice_onshipping()
