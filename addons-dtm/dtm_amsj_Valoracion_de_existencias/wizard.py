from datetime import datetime
from openerp import tools
from openerp.osv import fields, osv
from openerp.tools.translate import _


class wizard_valuation_history(osv.osv_memory):
    _name = 'wizard.valuation.history.dtm'
    # _description = 'Wizard that opens the stock valuation history table'
    _columns = {
        # 'choose_date': fields.boolean('Choose a Particular Date'),
        'date': fields.datetime('Date', required=True),
        'location_id': fields.many2one('stock.location', 'Parent Location', select=True,
                                       domain="[('laboratorio_id','!=',False)]"),
        'sector_id': fields.many2one('categoria', 'Sector', select=True),

    }

    _defaults = {
        # 'choose_date': False,
        'date': fields.datetime.now,
    }

    def open_table(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        ctx = context.copy()
        ctx['history_date'] = data['date']
        ctx['search_default_group_by_product'] = True
        # ctx['search_default_group_by_location'] = True
        # valor = int(data['location_id'][0])
        return {
            'domain': "[('date', '<=', '" + data['date'] + "'),('location_id','='," + str(
                data['location_id'][0]) + "),('sector_id','='," + str(data['sector_id'][0]) + ")]",
            'name': _('Stock Value At Date'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.history.dtm',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }


class stock_history_dtm(osv.osv):
    _name = 'stock.history.dtm'
    _auto = False
    _order = 'date asc'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False,
                   lazy=True):
        res = super(stock_history_dtm, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit,
                                                        context=context, orderby=orderby, lazy=lazy)
        if context is None:
            context = {}
        date = context.get('history_date', datetime.now())
        if 'inventory_value' in fields:
            group_lines = {}
            for line in res:
                domain = line.get('__domain', domain)
                group_lines.setdefault(str(domain), self.search(cr, uid, domain, context=context))
            line_ids = set()
            for ids in group_lines.values():
                for product_id in ids:
                    line_ids.add(product_id)
            line_ids = list(line_ids)
            lines_rec = {}
            if line_ids:
                cr.execute(
                    'SELECT id, product_id, price_unit_on_quant, company_id, quantity FROM stock_history WHERE id in %s',
                    (tuple(line_ids),))
                lines_rec = cr.dictfetchall()
            lines_dict = dict((line['id'], line) for line in lines_rec)
            product_ids = list(set(line_rec['product_id'] for line_rec in lines_rec))
            products_rec = self.pool['product.product'].read(cr, uid, product_ids, ['cost_method', 'product_tmpl_id'],
                                                             context=context)
            products_dict = dict((product['id'], product) for product in products_rec)
            cost_method_product_tmpl_ids = list(
                set(product['product_tmpl_id'][0] for product in products_rec if product['cost_method'] != 'real'))
            histories = []
            if cost_method_product_tmpl_ids:
                cr.execute(
                    'SELECT DISTINCT ON (product_template_id, company_id) product_template_id, company_id, cost FROM product_price_history WHERE product_template_id in %s AND datetime <= %s ORDER BY product_template_id, company_id, datetime DESC',
                    (tuple(cost_method_product_tmpl_ids), date))
                histories = cr.dictfetchall()
            histories_dict = {}
            for history in histories:
                histories_dict[(history['product_template_id'], history['company_id'])] = history['cost']
            for line in res:
                inv_value = 0.0
                lines = group_lines.get(str(line.get('__domain', domain)))
                for line_id in lines:
                    line_rec = lines_dict[line_id]
                    product = products_dict[line_rec['product_id']]
                    if product['cost_method'] == 'real':
                        price = line_rec['price_unit_on_quant']
                    else:
                        price = histories_dict.get((product['product_tmpl_id'][0], line_rec['company_id']), 0.0)
                    inv_value += price * line_rec['quantity']
                line['inventory_value'] = inv_value
        return res

    def _get_inventory_value(self, cr, uid, ids, name, attr, context=None):
        if context is None:
            context = {}
        date = context.get('history_date')
        product_tmpl_obj = self.pool.get("product.template")
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_id.cost_method == 'real':
                res[line.id] = line.quantity * line.price_unit_on_quant
            else:
                res[line.id] = line.quantity * product_tmpl_obj.get_history_price(cr, uid,
                                                                                  line.product_id.product_tmpl_id.id,
                                                                                  line.company_id.id, date=date,
                                                                                  context=context)
        return res

    _columns = {
        'move_id': fields.many2one('stock.move', 'Stock Move', required=True),
        'location_id': fields.many2one('stock.location', 'Location', required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_categ_id': fields.many2one('product.category', 'Product Category', required=True),
        'quantity': fields.float('Product Quantity'),
        'date': fields.datetime('Operation Date'),
        'price_unit_on_quant': fields.float('Value', group_operator='avg'),
        'inventory_value': fields.function(_get_inventory_value, string="Inventory Value", type='float', readonly=True),
        'source': fields.char('Source'),
        'sector_id': fields.many2one('categoria', 'Sector')

    }

    def init2(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history_dtm')
        cr.execute("""
           SELECT min(foo.id) AS id,
    foo.move_id,
    foo.location_id,
    foo.company_id,
    foo.product_id,
    foo.product_categ_id,
    sum(foo.quantity) AS quantity,
    foo.date,
    COALESCE(sum(foo.price_unit_on_quant * foo.quantity) / NULLIF(sum(foo.quantity), 0::double precision), 0::double precision) AS price_unit_on_quant,
    foo.source,
    foo.sector_id
   FROM ( SELECT stock_move.id,
            stock_move.id AS move_id,
            dest_location.id AS location_id,
            dest_location.company_id,
            stock_move.product_id,
            product_template.categ_id AS product_categ_id,
            quant.qty AS quantity,
            stock_move.date,
            quant.cost AS price_unit_on_quant,
            stock_move.origin AS source,
            product_template.categoria_id AS sector_id
           FROM stock_move
             JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = stock_move.id
             JOIN stock_quant quant ON stock_quant_move_rel.quant_id = quant.id
             JOIN stock_location dest_location ON stock_move.location_dest_id = dest_location.id
             JOIN stock_location source_location ON stock_move.location_id = source_location.id
             JOIN product_product ON product_product.id = stock_move.product_id
             JOIN product_template ON product_template.id = product_product.product_tmpl_id
          WHERE quant.qty > 0::double precision AND stock_move.state::text = 'done'::text AND (dest_location.usage::text = ANY (ARRAY['internal'::character varying::text, 'transit'::character varying::text])) AND (NOT (source_location.company_id IS NULL AND dest_location.company_id IS NULL) OR source_location.company_id <> dest_location.company_id OR (source_location.usage::text <> ALL (ARRAY['internal'::character varying::text, 'transit'::character varying::text])))
        UNION ALL
         SELECT '-1'::integer * stock_move.id AS id,
            stock_move.id AS move_id,
            source_location.id AS location_id,
            source_location.company_id,
            stock_move.product_id,
            product_template.categ_id AS product_categ_id,
            - quant.qty AS quantity,
            stock_move.date,
            quant.cost AS price_unit_on_quant,
            stock_move.origin AS source,
            product_template.categoria_id AS sector_id
           FROM stock_move
             JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = stock_move.id
             JOIN stock_quant quant ON stock_quant_move_rel.quant_id = quant.id
             JOIN stock_location source_location ON stock_move.location_id = source_location.id
             JOIN stock_location dest_location ON stock_move.location_dest_id = dest_location.id
             JOIN product_product ON product_product.id = stock_move.product_id
             JOIN product_template ON product_template.id = product_product.product_tmpl_id
          WHERE quant.qty > 0::double precision AND stock_move.state::text = 'done'::text AND (source_location.usage::text = ANY (ARRAY['internal'::character varying::text, 'transit'::character varying::text])) AND (NOT (dest_location.company_id IS NULL AND source_location.company_id IS NULL) OR dest_location.company_id <> source_location.company_id OR (dest_location.usage::text <> ALL (ARRAY['internal'::character varying::text, 'transit'::character varying::text])))) foo
  GROUP BY foo.move_id, foo.location_id, foo.company_id, foo.product_id, foo.product_categ_id, foo.date, foo.source, foo.sector_id;

            )""")
