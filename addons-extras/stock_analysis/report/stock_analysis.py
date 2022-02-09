# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import tools
from openerp import models, fields


class StockAnalysis(models.Model):
    _name = 'stock.analysis'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string='Producto', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Ubicación', readonly=True)
    qty = fields.Float(string='Cantidad', readonly=True)
    lot_id = fields.Many2one(
        'stock.production.lot', string='Lote', readonly=True)
    package_id = fields.Many2one(
        'stock.quant.package', string='Paquete', readonly=True)
    in_date = fields.Datetime('Fecha entrante', readonly=True)
    categ_id = fields.Many2one(
        'product.category', string='Categoria', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Compania', readonly=True)
    tipo_empaque_id = fields.Many2one('tipo.empaque', 'Tipo de Empaque', readonly=True)

    tipo_id = fields.Many2one(
        'tipo', string='Tipo', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """CREATE or REPLACE VIEW %s as (
            SELECT
                quant.id AS id,
                quant.product_id AS product_id,
                quant.location_id AS location_id,
                quant.qty AS qty,
                quant.lot_id AS lot_id,
                quant.package_id AS package_id,
                quant.in_date AS in_date,
                quant.company_id,
                template.categ_id AS categ_id,
                template.tipo_id AS tipo_id,
                template.tipo_de_empaque AS tipo_empaque_id
            FROM stock_quant AS quant
            JOIN product_product prod ON prod.id = quant.product_id
            JOIN product_template template
                ON template.id = prod.product_tmpl_id
            INNER JOIN tipo t ON t.id = template.tipo_id
            )"""
            % (self._table)
        )


class ConsumosAnalysis(models.Model):
    _name = 'consumos.analysis'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string='Producto', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Ubicación', readonly=True , index=True)

    qty = fields.Float(string='Cantidad', readonly=True)

    out_date = fields.Datetime('Fecha', readonly=True, index=True)
    # categ_id = fields.Many2one(
    #     'product.category', string='Categoria', readonly=True)

    familia_id = fields.Many2one('familia', 'Familia', index=True, readonly=True)
    principio_activo_id = fields.Many2one('principio.activo', 'Genérico', index=True, readonly=True)
    grupo_id = fields.Many2one('grupo', 'Grupo', readonly=True)
    subgrupo_id = fields.Many2one('subgrupo', 'Subgrupo', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure',
                                  readonly=True, related=('product_id', 'uom_id'))

    categoria_id = fields.Many2one('categoria', 'Categoria',readonly=True)
    tipo_empaque_id = fields.Many2one('tipo.empaque', 'Tipo de Empaque', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """CREATE or REPLACE VIEW %s as (
            SELECT 
                m.id AS id,
                m.product_id AS product_id,
                m.location_id AS location_id,
                pt.uom_id AS product_uom,
                m.date AS out_date,
                pt.familia_id AS familia_id,
                pt.principio_activo_id AS principio_activo_id,
                pt.grupo_id AS grupo_id,
                pt.subgrupo_id AS subgrupo_id,
                pt.categoria_id AS categoria_id,
                m.product_qty AS qty,
                pt.tipo_de_empaque AS tipo_empaque_id
                FROM stock_move m
                INNER JOIN product_product p ON p.id = m.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN stock_location l on l.id = m.location_id
                INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
                
                WHERE (coalesce(l2.scrap_location,false) = true OR l2.usage = 'customer')
            )"""
            % (self._table)
        )


class SicofarmacosAnalysis(models.Model):
    _name = 'sicofarmacos.analysis'
    _table = 'dtm_sicofarmacos'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string='Producto', readonly=True)
    location_id = fields.Many2one(
        'stock.location', string='Ubicación', readonly=True , index=True)


    qty = fields.Float(string='Cantidad', readonly=True)

    out_date = fields.Datetime('Fecha', readonly=True, index=True)
    # categ_id = fields.Many2one(
    #     'product.category', string='Categoria', readonly=True)

    # tipo_empaque_id = fields.Many2one('tipo_empaque', 'Tipo de empaque', index=True, readonly=True)
    familia_id = fields.Many2one('familia', 'Familia', index=True, readonly=True)
    principio_activo_id = fields.Many2one('principio.activo', 'Genérico', index=True, readonly=True)
    grupo_id = fields.Many2one('grupo', 'Grupo', readonly=True)
    subgrupo_id = fields.Many2one('subgrupo', 'Subgrupo', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure',
                                  readonly=True, related=('product_id', 'uom_id'))

    categoria_id = fields.Many2one('categoria', 'Categoria',readonly=True)
    tipo_empaque_id = fields.Many2one('tipo.empaque', 'Tipo de Empaque', readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'dtm_sicofarmacos')
        cr.execute(
            """CREATE or REPLACE VIEW dtm_sicofarmacos as (
             SELECT 
                m.id AS id,
                m.product_id AS product_id,
                m.location_id AS location_id,
                pt.uom_id AS product_uom,
                m.date AS out_date,
                pt.familia_id AS familia_id,
                pt.principio_activo_id AS principio_activo_id,
                pt.grupo_id AS grupo_id,
                pt.subgrupo_id AS subgrupo_id,
                pt.categoria_id AS categoria_id,
                m.product_qty AS qty,
                pt.tipo_de_empaque AS tipo_empaque_id
                FROM stock_move m
                INNER JOIN product_product p ON p.id = m.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN stock_location l on l.id = m.location_id
                INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
                INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
                INNER JOIN tipo t ON t.id = pt.tipo_id
                LEFT JOIN subgrupo sg ON sg.id = pt.subgrupo_id
                WHERE (coalesce(l2.scrap_location,false) = true OR l2.usage = 'customer')
      AND (lower(t.name) like '%sicof%')
      AND (pt.subgrupo_id is null OR sg."CodigoAMSJ" not in ('1505'::character varying, '5103'::character varying))
            )"""

        )

class EstupefacientesAnalysis(models.Model):
    _name = 'estupefacientes.analysis'
    _table = 'dtm_estupefacientes'
    _auto = False
    _rec_name = 'product_id'

    product_id = fields.Many2one(
        'product.product', string='Producto', readonly=True)

    qty = fields.Float(string='Cantidad', readonly=True)

    out_date = fields.Datetime('Fecha', readonly=True, index=True)
    # categ_id = fields.Many2one(
    #     'product.category', string='Categoria', readonly=True)

    location_id = fields.Many2one(
        'stock.location', string='Ubicación', readonly=True, index=True)

    familia_id = fields.Many2one('familia', 'Familia', index=True, readonly=True)
    principio_activo_id = fields.Many2one('principio.activo', 'Genérico', index=True, readonly=True)
    grupo_id = fields.Many2one('grupo', 'Grupo', readonly=True)
    subgrupo_id = fields.Many2one('subgrupo', 'Subgrupo', readonly=True)
    product_uom = fields.Many2one('product.uom', 'Unit of Measure',
                                  readonly=True, related=('product_id', 'uom_id'))

    categoria_id = fields.Many2one('categoria', 'Categoria',readonly=True)
    tipo_empaque_id = fields.Many2one('tipo.empaque','Tipo de Empaque',readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'dtm_estupefacientes')
        cr.execute(
            """CREATE or REPLACE VIEW dtm_estupefacientes as (
             SELECT 
                m.id AS id,
                m.product_id AS product_id,
                l.id AS location_id,
                pt.uom_id AS product_uom,
                m.date AS out_date,
                pt.familia_id AS familia_id,
                pt.principio_activo_id AS principio_activo_id,
                pt.grupo_id AS grupo_id,
                pt.subgrupo_id AS subgrupo_id,
                pt.categoria_id AS categoria_id,
                m.product_qty AS qty,
                pt.tipo_de_empaque AS tipo_empaque_id
                FROM stock_move m
                INNER JOIN product_product p ON p.id = m.product_id
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN stock_location l on l.id = m.location_id
                INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
                INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
                INNER JOIN tipo t ON t.id = pt.tipo_id
                LEFT JOIN subgrupo sg ON sg.id = pt.subgrupo_id
                WHERE (coalesce(l2.scrap_location,false) = true OR l2.usage = 'customer')
      AND (lower(t.name) like '%estupefacien%')
      AND (pt.subgrupo_id is null OR sg."CodigoAMSJ" not in ('1505'::character varying, '5103'::character varying)) )"""

        )

