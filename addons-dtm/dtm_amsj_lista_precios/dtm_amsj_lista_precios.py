#  -*- coding: utf-8 -*-
from openerp import models,fields,api
import openerp.tools as tools


class dtm_amsj_lista_precios(models.Model):
    _name = "dtm.amsj.lista.precios"
    _rec_name = 'producto_id'
    _auto = False


    producto_id = fields.Many2one('product.product',string='Producto')
    generico = fields.Char(string=u'Genérico',readonly=True )
    forma_farmaceutica_id = fields.Many2one('forma.farmaceutica',string=u'Forma Farmacéutica',readonly=True )
    concentracion_valor = fields.Float(u'Valor de Concentración')
    concentracion_unidad = fields.Many2one('product.uom', string=u'Unidad de medida Concentración')
    precio = fields.Float(u'Precio de Costo')
    precio_cocemi = fields.Float(u'Precio COCEMI')
    puc = fields.Float(u'Precio Ultima Compra')
    precio_oferta = fields.Float(u'Precio Oferta')
    promedio  = fields.Integer(u'Promedio Consumo Anual')
    proveedor_id = fields.Many2one('res.partner',string=u"Proveedor")
    stock_actual = fields.Integer('Stock Actual SJM')

    def init2(self, cr):
        tools.drop_view_if_exists(cr, 'dtm_amsj_lista_precios')
        cr.execute("""
            CREATE OR REPLACE VIEW public.dtm_amsj_lista_precios AS 
SELECT row_number() over () as id,
                    p.id as producto_id,
                    
                    pt.principio_activo_id,
                    pt.forma_farmaceutica_id,
                    pt.concentracion_valor,
                    pt.concentracion_unidad,
                    
                    ptp.precio,
                    pt.precio_cocemi,
                    sp.price_unit as puc,
                    po.price_unit as precio_oferta,
                    ca.promedio,
                    rp.id as proveedor_id,
                    stk.qty as stock_actual
                    
                FROM product_product p
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN tipo_empaque te ON te.id = pt.tipo_de_empaque
                LEFT JOIN product_uom uom ON uom.id = pt.concentracion_unidad
                LEFT JOIN principio_activo pa ON pa.id = pt.principio_activo_id
                LEFT JOIN forma_farmaceutica ff ON ff.id = pt.forma_farmaceutica_id
                LEFT JOIN dtm_precio_producto as ptp ON ptp.product_tmpl_id = pt.id
                LEFT JOIN dtm_precio_ultima_compra AS sp ON pt.id = sp.product_tmpl_id
                LEFT JOIN dtm_precio_oferta AS po ON pt.id = po.product_tmpl_id
                LEFT JOIN dtm_promedio_anual_consumo as ca on pt.id = ca.product_tmpl_id
                LEFT JOIN product_supplierinfo psi ON psi.product_tmpl_id = pt.id
                LEFT JOIN res_partner rp ON rp.id = psi.name
                JOIN dtm_stock_sjm stk ON stk.product_tmpl_id = pt.id
                 WHERE pt.categoria_id = 17 AND pt.purchase_ok = true AND p.active = true;    

ALTER TABLE public.dtm_amsj_lista_precios
  OWNER TO odoo;

            """)

    #     tools.drop_view_if_exists(cr, 'dtm_amsj_lista_precios')
    #     cr.execute("""
    #      CREATE OR REPLACE VIEW public.dtm_amsj_lista_precios AS
    #             SELECT row_number() over () as id,
    #                 p.id as product_id,
    #                 pt.principio_activo_id,
    #                 pt.forma_farmaceutica_id,
    #                 pt.concentracion_valor,
    #                 pt.concentracion_unidad,
    #                 ptp.precio,
    #                 pt.precio_cocemi,
    #                 sp.price_unit as puc,
    #                 po.price_unit as precio_oferta,
    #                 ca.promedio
    #             FROM product_product p
    #             INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
    #             INNER JOIN tipo_empaque te ON te.id = pt.tipo_de_empaque
    #             LEFT JOIN product_uom uom ON uom.id = pt.concentracion_unidad
    #             LEFT JOIN principio_activo pa ON pa.id = pt.principio_activo_id
    #             LEFT JOIN forma_farmaceutica ff ON ff.id = pt.forma_farmaceutica_id
    #             LEFT JOIN dtm_precio_producto as ptp ON ptp.product_tmpl_id = pt.id
    #             LEFT JOIN dtm_precio_ultima_compra AS sp ON pt.id = sp.product_tmpl_id
    #             LEFT JOIN dtm_precio_oferta AS po ON pt.id = po.product_tmpl_id
    #             left join dtm_promedio_anual_consumo as ca on pt.id = ca.product_tmpl_id and pt.categoria_id = ca.categoria_id
    #             WHERE pt.categoria_id = 17 and pt.purchase_ok = True and p.active = True;
    #         """)

