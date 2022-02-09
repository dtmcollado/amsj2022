# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Datamatic All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from datetime import datetime, date, timedelta
from openerp import tools

class dtm_amsj_consumo_de_productos(models.Model):
    _inherit = 'stock.move'
    #
    # def init_no_usar(self, cr):
    #     tools.drop_view_if_exists(cr, 'consumos_report')
    #     cr.execute("""
    #      create or replace view consumos_report as (
    #            SELECT  c.name as sector,t.name as categoria_interna,
    #             pt.id as product_template_id,pt.name as product_template_name,
    #             via_admin.name as  via_de_administracion,
    #             pt.sema_ucor,pt.codigo_geosalud,prin_activo.name as principio_activo,
    #             fa.name as familia,gr.name as grupo,
    #             sub.name as subgrupo,forma.name as forma_farmaceutica,
    #             m.product_qty,
    #             replace(l.complete_name,'Physical Locations / ','')::character varying  as origen,
	 #            replace(l2.complete_name,'Physical Locations / ','')::character varying  as destino,
	 #            m.centro_costos , quant.cost ,  quant.qty AS quantity,
	 #            c.id as sector_id,pt.categ_id as categoria_interna_id,gr.id as grupo_id,
	 #            sub.id as subgrupo_id,forma.id as forma_farmaceutica_id , prin_activo.id as principio_activo_id,
	 #            fa.id as familia_id , m.date as fecha , pt.ftm as ftm , l2.id as destino_id,l.id as origen_id,
	 #            p.default_code as CodMSP,
	 #            quant.qty*m.price_unit::numeric(18,2) AS total_fifo,
	 #            quant.qty*ip.value_float::numeric(18,2) as total_ultima_compra
    #         FROM public.stock_move m
    #   INNER JOIN stock_location l ON l.id = m.location_id
    #   INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
    #   INNER JOIN product_product p ON p.id = m.product_id
    #   INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
    #   INNER JOIN product_category t ON t.id = pt.categ_id
    #   INNER JOIN ir_property as ip ON (ip.res_id = 'product.template,' || p.product_tmpl_id)
    #   INNER JOIN ir_model_fields imf ON (imf.id = ip.fields_id AND imf.name = 'standard_price')
    #   LEFT JOIN categoria c ON c.id = pt.categoria_id
    #   LEFT JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = m.id
    #   LEFT JOIN stock_quant quant ON stock_quant_move_rel.quant_id = quant.id
    #   LEFT JOIN grupo gr ON pt.grupo_id = gr.id
    #   LEFT JOIN via_de_administracion via_admin ON pt.via_de_administracion = via_admin.id
    #   LEFT JOIN principio_activo prin_activo ON pt.principio_activo_id = prin_activo.id
    #   LEFT JOIN familia fa ON pt.familia_id = fa.id
    #   LEFT JOIN subgrupo sub ON pt.subgrupo_id = sub.id
    #   LEFT JOIN forma_farmaceutica forma ON pt.forma_farmaceutica_id = forma.id
    #   WHERE l2.scrap_location = true)"""
    # )

    @api.model
    def create(self, vals):
        destino = self.env['stock.location'].browse(vals.get('location_dest_id'))
        vals['destino_de_consumo'] = destino.scrap_location
        vals['valor_total'] = float(vals.get('product_qty', 0)) * float(vals.get('price_unit', 0))
        return super(dtm_amsj_consumo_de_productos, self).create(vals)

    @api.multi
    def compute_valor_total(self):
        for rec in self:
            if not rec.valor_total:
                rec.write({'valor_total': rec.product_qty * rec.price_unit})
            if not rec.almacen_origen:
                rec.write({'almacen_origen': rec.location_id.location_id.id})
            wharehouse = self.env['stock.warehouse'].search([
                ('wh_input_stock_loc_id', '=', rec.location_id.id)
            ])
            rec.write({'centro_costos': wharehouse.centro_costos})

    @api.one
    @api.depends('date')
    def get_mes(self):
        if self.date:
            meses = {'01': 'enero',
                     '02': 'febrero',
                     '03': 'marzo',
                     '04': 'abril',
                     '05': 'mayo',
                     '06': 'junio',
                     '07': 'julio',
                     '08': 'agosto',
                     '09': 'setiembre',
                     '10': 'octubre',
                     '11': 'noviembre',
                     '12': 'diciembre',
                     }
            try:
                mes = meses.get(datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').strftime('%m'))
            except:
                mes = meses.get(datetime.strptime(self.date, '%Y-%m-%d').strftime('%m'))
            self.mes_calculado = mes
            self.write({'mes': mes})

    @api.one
    @api.depends('date')
    def get_anio(self):
        if self.date:
            try:
                self.anio_calculado = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').strftime('%Y')
            except:
                self.anio_calculado = datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y')
            self.anio = self.anio_calculado
            self.write({'anio': self.anio_calculado})

    centro_costos = fields.Char(string=u"Centro de costos", store=True)
    almacen_origen = fields.Many2one(comodel_name='stock.location', string=u"Almacén", store=True)
    valor_total = fields.Float(string="Precio por Cantidad", store=True)
    
    destino_de_consumo = fields.Boolean(string="La ubicación Destino es de consumo",
                                        related='location_dest_id.scrap_location')

    compute = fields.Boolean(string="solo para cargas", compute='compute_valor_total')

    mes_calculado = fields.Char(string='mes', compute='get_mes')
    mes = fields.Char(string='mes', store=True)
    anio_calculado = fields.Integer(string='mes', compute='get_anio')
    anio = fields.Integer(string=u'año', store=True)


dtm_amsj_consumo_de_productos()

# """
# SELECT  t.name,sum(m.product_qty),
# 	m.location_id,m.location_dest_id, m.centro_costos, m.familia_id,
#        m.generico_id
#   FROM public.stock_move m
#       INNER JOIN stock_location l ON l.id = m.location_id
#       INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
#       INNER JOIN product_product p ON p.id = m.product_id
#       INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
#       INNER JOIN tipo t ON t.id = pt.tipo_id
#       WHERE l2.scrap_location = true
#   GROUP BY t.name,m.location_id,m.location_dest_id, m.centro_costos, m.familia_id,
#        m.generico_id ;
# """

