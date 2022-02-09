#  -*- coding: utf-8 -*-
from openerp import models,fields,api
import openerp.tools as tools




class dtm_amsj_stock_de_genericos(models.Model):
    _name = "dtm.amsj.stock.de.genericos"
    # _rec_name = 'name_forma_farmaceutica'
    _auto = False

    ubicacion_id = fields.Many2one('stock.location', string='Ubicación', readonly=True)
    principio_activo_id = fields.Many2one('principio.activo', string='Generico', readonly=True)
    forma_farmaceutica_id = fields.Many2one('forma.farmaceutica', string=u'Forma farmacéutica', readonly=True)
    concentracion_valor = fields.Float(u'Valor de Concentración')
    concentracion_unidad = fields.Integer(u'Unidad de medida Concentración')
    stock_maximo = fields.Integer(u'Stock Critico')
    stock_actual = fields.Integer(u'Stock Actual')
    diferencia = fields.Integer()


    def init2(self, cr):

        tools.drop_view_if_exists(cr, 'dtm_amsj_stock_de_genericos')
        cr.execute("""
            CREATE OR REPLACE VIEW public.dtm_amsj_stock_de_genericos AS 
 SELECT 
    row_number() OVER () AS id,
    l.ubicacion_id,
    pt.principio_activo_id,
    pt.forma_farmaceutica_id,
    pt.concentracion_valor,
    pt.concentracion_unidad,
    sum(l.stock_critico)::numeric AS stock_maximo,
    sum(sq.qty)::numeric AS stock_actual
   FROM ubicacion_stockcritico l
     JOIN product_template pt ON pt.id = l.product_tmpl_id and l.rmc = False
     JOIN ( SELECT sq_1.location_id,
            pt_1.principio_activo_id,
            pt_1.forma_farmaceutica_id,
            pt_1.concentracion_valor,
            pt_1.concentracion_unidad,
            sum(sq_1.qty) AS qty
           FROM stock_quant sq_1
             JOIN product_product p ON p.id = sq_1.product_id
             JOIN product_template pt_1 ON pt_1.id = p.product_tmpl_id
             INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque and not lower(te.name) like 'unitario'
			
          GROUP BY sq_1.location_id, pt_1.principio_activo_id, pt_1.forma_farmaceutica_id, pt_1.concentracion_valor, pt_1.concentracion_unidad) sq ON l.ubicacion_id = sq.location_id AND pt.principio_activo_id = sq.principio_activo_id AND pt.forma_farmaceutica_id = sq.forma_farmaceutica_id AND pt.concentracion_valor = sq.concentracion_valor AND pt.concentracion_unidad = sq.concentracion_unidad
     --JOIN principio_activo pa ON pa.id = sq.principio_activo_id
     --JOIN forma_farmaceutica ff ON ff.id = sq.forma_farmaceutica_id
  GROUP BY l.ubicacion_id, pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad;

            """)

        # cr.execute("""
        #
     #    CREATE OR REPLACE VIEW public.dtm_amsj_stock_de_genericos AS
 	# SELECT row_number() over () as id, sw.name as almacen, sl.name as ubicacion ,c.name as sector, pa.name as principio_activo, pt.name as producto, coalesce(SUM(sq.qty),0) as stock
     #            FROM stock_quant sq
     #
     #            INNER JOIN stock_location sl ON sl.id = sq.location_id
     #            INNER JOIN stock_warehouse sw ON sw.id = sl.almacen_id
     #            INNER JOIN product_product p ON p.id = sq.product_id
     #            INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
     #            INNER JOIN categoria C ON c.id = pt.categoria_id
     #            INNER JOIN tipo_empaque te ON te.id = pt.tipo_de_empaque AND lower(te.name) = 'caja'
     #            INNER JOIN principio_activo pa ON pa.id = pt.principio_activo_id
     #
     #            WHERE (coalesce(sl.scrap_location,false) = false AND sl.usage != 'customer')
     #            GROUP BY sw.name, sl.name, pa.name, c.name, pt.name
     #            order by sw.name, sl.name
     #
     #    """)

    @api.multi
    def ver_productos(self):

        view = self.env.ref('dtm_amsj_stock_de_genericos.stock_genericos_wizard')


        ff = self.forma_farmaceutica_id[0].id

        # ff = self.env['forma.farmaceutica'].search([('name','=',self.name_forma_farmaceutica)])
        # forma_farmaceutica_id = False
        # if ff:
        #     forma_farmaceutica_id = ff[0].id
        #
        stock= self.env['ubicacion.stockcritico'].search([
            ('ubicacion_id','=',self.ubicacion_id[0].id),
            ('forma_farmaceutica_id','=',self.forma_farmaceutica_id[0].id),
            ('generico_id','=',self.principio_activo_id[0].id),
            ('rmc','=',False),
            ('concentracion_valor','=',self.concentracion_valor),
            ('concentracion_unidad','=',self.concentracion_unidad)])
        lista=[]

        for i in stock:
            lista.append(i.id)

        return {
            'name':("Stock Genericos"),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'dtm.amsj.stock.de.genericos.wizard',
            'views': [(view.id, 'form')],
            'view_id': False,
            'target': 'new',
            'nodestroy': True,
            'context': {'lista':lista},

        }

class dtm_amsj_stock_de_genericos_wizard(models.TransientModel):
    _name = "dtm.amsj.stock.de.genericos.wizard"
    #stock_critico = fields.One2many("ubicacion.stockcritico", "product_tmlp_id")
    #stock_critico = fields.Many2many(comodel_name='ubicacion.stockcritico',relation='ubi_st_ritico_rel_', string='')
    mostrar=fields.Html(string='Tabla', readonly=True)
    mostrar_stock=fields.Html(string='Tabla', readonly=True)



    # @api.onchange("stock_critico")
    # def get_domain(self):
    #     print 'contexto campo --> ', self._context.get('lista')
    #     return {
    #         "domain": {
    #             "stock_critico": [("id", "in", self._context.get('lista'))],
    #         }
    #     }
    @api.multi
    @api.onchange("mostrar")
    def get_mostar(self):
        stock_critico = self.env['ubicacion.stockcritico'].search([("id", "in", self._context.get('lista'))])
        # print 'contexto --> HTML ', self._context.get('lista')
        # print stock_critico, 'HTML'

        reporte  = '<h2>Productos que se controla stock maximo</h2>'
        reporte += '<table style="width:100%;">'
        reporte += '   <thead style="border: thin solid gray;">'
        reporte += '        <tr style="border: thin solid gray;">'
        reporte += '            <th colspan="4" style="border: thin solid gray; text-align: center">Producto</th>'
        reporte += '            <th style="border: thin solid gray; text-align: center">Generico</th>'
        reporte += '            <th style="border: thin solid gray; text-align: center">Forma Farmaceutica</th>'
        reporte += '            <th style="border: thin solid gray; text-align: center">Concentracion Valor</th>'
        reporte += '            <th style="border: thin solid gray; text-align: center">Concentracion Unidad</th>'
        reporte += '            <th style="border: thin solid gray; text-align: center">Stock Maximo</th>'
        reporte += '        </tr style="border: thin solid gray;">'
        reporte += '    </thead>'
        reporte += '    <tbody>'

        ubicacion_id = forma_farmaceutica_id = principio_activo_id = concentracion_valor = concentracion_unidad =  None

        for i in stock_critico:
            ubicacion_id =i.ubicacion_id.id
            forma_farmaceutica_id =i.forma_farmaceutica_id.id
            principio_activo_id = i.generico_id.id
            concentracion_valor = i.concentracion_valor
            concentracion_unidad = i.concentracion_unidad.id

            reporte += '        <tr style="border-bottom: thin solid gray;">'
            reporte += '            <td colspan="4" style="text-align: center; vertical-align: middle;">%s</td>' % (i.product_tmpl_id.name)
            reporte += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (i.generico_id.name)
            reporte += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (i.forma_farmaceutica_id.name)
            reporte += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (i.concentracion_valor)
            reporte += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (i.concentracion_unidad.name)
            reporte += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (i.stock_critico)
            reporte += '        </tr>'
        reporte += '    </tbody>'

        reporte += '</table ></br></br></br></br></br></br><hr>'
        self.mostrar=reporte

        reporte_stock=''
        reporte_stock += '<h2>Productos con Stock</h2>'
        reporte_stock += '<table style="width:100%;">'
        reporte_stock += '   <thead style="border: thin solid gray;">'
        reporte_stock += '        <tr style="border: thin solid gray;">'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center" colspan="2">Producto</th>'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center">Generico</th>'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center">Forma Farmaceutica</th>'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center">Concentracion Valor</th>'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center">Concentracion Unidad</th>'
        reporte_stock += '            <th style="border: thin solid gray; text-align: center">Stock</th>'
        reporte_stock += '        </tr style="border: thin solid gray;">'
        reporte_stock += '    </thead>'
        reporte_stock += '    <tbody>'



        sql='''SELECT pt.name as producto, pa.name as generico, ff.name as forma_farmaceutica,
                    pt.concentracion_valor, pu.name as unidad, SUM(qty) as stock
                FROM stock_quant sq
                INNER JOIN product_product p ON p.id = sq.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN principio_activo pa ON pa.id = pt.principio_activo_id
                INNER JOIN forma_farmaceutica ff ON ff.id = pt.forma_farmaceutica_id
                INNER JOIN product_uom pu ON pu.id = pt.concentracion_unidad
            WHERE  sq.location_id= %(ubicacion_id)s AND pt.forma_farmaceutica_id = %(forma_farmaceutica_id)s AND pt.principio_activo_id = %(principio_activo_id)s AND pt.concentracion_valor = %(concentracion_valor)s AND concentracion_unidad = %(concentracion_unidad)s
            GROUP BY pt.name, pa.name, ff.name, pt.concentracion_valor, pu.name'''

        self.env.cr.execute(sql, {'ubicacion_id': ubicacion_id,'forma_farmaceutica_id': forma_farmaceutica_id ,'principio_activo_id': principio_activo_id,'concentracion_valor': concentracion_valor,'concentracion_unidad': concentracion_unidad})
        sql_qty = self.env.cr.fetchall()
        #print sql_qty
        if sql_qty:

            for x in sql_qty:
                reporte_stock += '        <tr style="border-bottom: thin solid gray;">'
                reporte_stock += '            <td colspan="2" style="text-align: center; vertical-align: middle;">%s</td>' % (x[0])
                reporte_stock += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (x[1])
                reporte_stock += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (x[2])
                reporte_stock += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (x[3])
                reporte_stock += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (x[4])
                reporte_stock += '            <td style="text-align: center; vertical-align: middle;">%s</td>' % (x[5])
                reporte_stock += '        </tr>'

        reporte_stock += '    </tbody>'
        reporte_stock += '</table >'




        self.mostrar_stock=reporte_stock



