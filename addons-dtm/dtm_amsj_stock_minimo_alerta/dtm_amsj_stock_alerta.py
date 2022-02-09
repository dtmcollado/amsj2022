#  -*- coding: utf-8 -*-
from openerp import models, fields, api
import openerp.tools as tools


class dtm_amsj_stock_alerta(models.Model):
    _name = "dtm.amsj.stock.de.alerta"
    # _rec_name = 'principio_activo_id'
    _auto = False


    # @api.multi
    # # @api.depends('purchase_order_qty')
    # def _get_diferecia(self):
    #     for each in self:
    #         if each.stock_actual <= each.stock_minimo:
    #             each.en_alerta = True
    #         else:
    #             each.en_alerta = False

    product_tmpl_id = fields.Many2one('product.template', string='Producto', readonly=True)
    principio_activo_id = fields.Many2one('principio.activo', string='Generico', readonly=True)
    forma_farmaceutica_id = fields.Many2one('forma.farmaceutica', string=u'Forma farmacéutica', readonly=True)
    concentracion_valor = fields.Float(u'Valor de Concentración')
    concentracion_unidad = fields.Integer(u'Unidad de medida Concentración')
    stock_minimo = fields.Integer(u'Stock Minimo')
    stock_actual = fields.Integer(u'Stock Actual')
    purchase_order_qty = fields.Integer(string=u'Cantidad en OC', related='product_tmpl_id.purchase_order_qty')
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    en_alerta = fields.Char(string='Estado')

    def init2(self, cr):
        tools.drop_view_if_exists(cr, 'dtm_amsj_stock_de_alerta')
        cr.execute("""
        CREATE OR REPLACE VIEW public.dtm_amsj_stock_de_alerta AS 
  SELECT row_number() OVER () AS id,
    l.product_tmpl_id,
    pt.principio_activo_id,
    pt.forma_farmaceutica_id,
    pt.concentracion_valor,
    pt.concentracion_unidad,
    l.stock_critico AS stock_minimo,
    st.qty AS stock_actual,
    0 as purchase_order_qty,
    p.id as product_id,
    (CASE WHEN  st.qty <= l.stock_critico THEN '*ALERTA*'
                      ELSE 'NORMAL'
                      END) as en_alerta
    
   FROM ubicacion_stockcritico l
     JOIN product_template pt ON pt.id = l.product_tmpl_id
     JOIN product_product  p  ON p.product_tmpl_id = l.product_tmpl_id
     LEFT JOIN dtm_stock_sjm st ON st.product_tmpl_id = l.product_tmpl_id
  WHERE l.ubicacion_id = 551
            """)


