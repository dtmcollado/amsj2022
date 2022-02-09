#  -*- coding: utf-8 -*-
from openerp import models,fields,api
import openerp.tools as tools




class dtm_amsj_stock_de_genericos_filial(models.Model):
    _name = "dtm.amsj.stock.maximo.filial"
    # _rec_name = 'name_forma_farmaceutica'
    _auto = False

    ubicacion_id = fields.Many2one('stock.location', string='Ubicación', readonly=True)
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string=u'Producto')
    principio_activo_id = fields.Many2one('principio.activo', string='Generico', readonly=True)
    forma_farmaceutica_id = fields.Many2one('forma.farmaceutica', string=u'Forma farmacéutica', readonly=True)
    concentracion_valor = fields.Float(u'Valor de Concentración')
    concentracion_unidad = fields.Integer(u'Unidad de medida Concentración')
    stock_maximo = fields.Integer(u'Stock Máximo')
    stock_actual = fields.Integer(u'Stock Actual')
    diferencia = fields.Integer()
    sector_id = fields.Many2one(string=u'Sector', comodel_name='categoria')
    product_id = fields.Many2one(
        'product.product', 'Producto',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]")

    def init(self, cr):

        tools.drop_view_if_exists(cr, 'dtm_amsj_stock_maximo_filial')
        cr.execute("""
            

CREATE OR REPLACE VIEW public.dtm_amsj_stock_maximo_filial AS 
 SELECT row_number() OVER () AS id,
    l.ubicacion_id,
    pt.id as product_tmpl_id,
    pt.principio_activo_id,
    pt.forma_farmaceutica_id,
    pt.concentracion_valor,
    pt.concentracion_unidad,
    sum(l.stock_critico)::numeric AS stock_maximo,
    sum(sq.qty)::numeric AS stock_actual,
        0 AS diferencia , pt.categoria_id as sector_id,
        p.id as product_id
   FROM ubicacion_stockcritico l
     JOIN product_template pt ON pt.id = l.product_tmpl_id
     JOIN product_product p   ON p.product_tmpl_id = l.product_tmpl_id
     JOIN ( SELECT p.product_tmpl_id,
    sum(COALESCE(sq.qty, 0::double precision)) AS qty , sq.location_id 
   FROM stock_quant sq
     JOIN product_product p ON p.id = sq.product_id
	GROUP BY sq.location_id, p.product_tmpl_id
 ) sq ON l.ubicacion_id = sq.location_id  AND pt.id = sq.product_tmpl_id
  GROUP BY l.ubicacion_id , pt.id , pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,pt.categoria_id,p.id;

ALTER TABLE public.dtm_amsj_stock_maximo_filial
  OWNER TO odoo;
GRANT ALL ON TABLE public.dtm_amsj_stock_maximo_filial TO odoo;

            """)





