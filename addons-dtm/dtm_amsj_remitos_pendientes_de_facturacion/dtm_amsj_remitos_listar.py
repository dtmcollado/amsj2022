#  -*- coding: utf-8 -*-
from openerp import models,fields,api
import openerp.tools as tools


class dtm_amsj_remitos_listar(models.Model):
    _name = "dtm.amsj.remitos.listar"
    _rec_name = 'order_name'
    _auto = False
    
    order_name = fields.Many2one('purchase.order',string='Nro Remito')
    default_code =  fields.Char(u'Codigo Producto')
    producto_id = fields.Many2one('product.product',string='Producto')
    product_qty =  fields.Integer(u'Cantidad')
    proveedor_id = fields.Many2one('res.partner',string=u"Proveedor")
    invoiced_qty = fields.Integer(u'Cantidad')
    price_unit = fields.Float(string='Precio')

   
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'dtm_amsj_remitos_listar')
        cr.execute("""
            CREATE OR REPLACE VIEW public.dtm_amsj_remitos_listar AS 
            SELECT row_number() over () as id,
            po.id as order_name,
            pp.default_code,
            pp.id as producto_id,
            pol.product_qty,
            rp.id as proveedor_id,
            pol.invoiced_qty,
            pol.price_unit
            from purchase_order po
            inner join purchase_order_line pol on po.id = pol.order_id
            inner join res_partner rp on rp.id = pol.partner_id
            inner join product_product pp on pp.id = pol.product_id
            where po.state in ('confirmed','approved','done')
            and pol.id not in (
                select purchase_line_id
                from account_invoice_line linea
                inner join account_invoice fact on fact.id = linea.invoice_id
                where not linea.purchase_line_id is null
                    and fact.state in ('open','paid')
                    )
            and pol.id in ( 
            select purchase_line_id from stock_move where state in ('confirmed','approved','done') 
            )
            order by po.name, pol.id
            """)

    @api.multi
    def ver_orden(self):

        view = self.env.ref('purchase.purchase_order_form')
        ff = self.order_name[0].id

             

        return {
                    'domain': "[('id', '=', " + str(ff) + ")]",
                    'name': 'Devolución Albarán',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'purchase.order',
                    'type': 'ir.actions.act_window',
                    # 'context': result,
                }