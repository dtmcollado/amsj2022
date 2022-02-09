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

import os
import base64

import xlwt
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO
from openerp import tools


class dtm_amsj_move(models.Model):
    _inherit = 'stock.move'

    # lot_id = fields.Many2one('stock.production.lot', 'Lot')
    # life_date = fields.Datetime(string='Life Date', related='lot_id.life_date')
    lote = fields.Char('Lote')

    @api.model
    def create(self, vals):
        if 'picking_id' in vals:
            pick = self.env['stock.picking'].search([
                                                 ('id', '=', vals['picking_id'])
                                             ])
            if not pick.sector_id:
                producto = self.env['product.product'].search([('id', '=', vals['product_id'])])
                pick.write({'sector_id': producto.categoria_id.id})

        return super(dtm_amsj_move, self).create(vals)


dtm_amsj_move()


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = "id desc"

    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")

    # def init(self, cr):
    #     tools.drop_view_if_exists(cr, 'consumos_report')
    #     cr.execute("""
    #       CREATE OR REPLACE FUNCTION sp_reponer(
    #             IN _location_id integer,
    #             IN _location_stock_id integer,
    #             IN _fecha_desde character varying,
    #             IN _fecha_hasta character varying)
    #           RETURNS TABLE(product_id integer, product_tmpl_id integer, uom_id integer, lot_id character varying, life_date date, qty integer) AS
    #         $BODY$
    #         DECLARE
    #
    #         --crear una tabla temporal para ir insertando los productos que voy a elegir
    #
    #         _elementos_cur record;
    #         _genericos_cur record;
    #         _sector_farmacia_id integer;
    #         _cantidad integer;
    #
    #         -- Manejando el error --
    #         _err_context text;
    #
    #         BEGIN
    #
    #             -- tabla temporal --
    #             DROP TABLE IF EXISTS tmp_productos;
    #             CREATE LOCAL TEMP TABLE tmp_productos
    #              ( product_id integer,
    #                product_tmpl_id integer,
    #                uom_id integer,
    #                lot_id character varying,
    #                life_date date,
    #                qty integer
    #              );
    #
    #
    #             -- variables ------------------------------------------------------------------------------------------------
    #             _sector_farmacia_id = (SELECT id FROM categoria WHERE lower(name) = 'farmacia' limit 1);
    #
    #
    #             FOR _elementos_cur IN
    #             SELECT m.product_id as product_id, p.product_tmpl_id, pt.uom_id as uom_id,
    #                 pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,
    #                 sum(m.product_qty) AS cantidad
    #             FROM stock_move m
    #             INNER JOIN product_product p ON p.id = m.product_id
    #             INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
    #             INNER JOIN stock_location l on l.id = m.location_id
    #             INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
    #             WHERE m.date >= _fecha_desde::date AND m.date <= _fecha_hasta::date
    #                 AND l.principal_del_expendio = true
    #                 AND pick.code <> 'incoming'
    #                 AND l.id=_location_id
    #                 AND pt.categoria_id = _sector_farmacia_id
    #             GROUP BY m.product_id, p.product_tmpl_id, pt.uom_id, pt.principio_activo_id, pt.forma_farmaceutica_id,
    #                 pt.concentracion_valor, pt.concentracion_unidad
    #
    #             LOOP
    #
    #                 _cantidad  := _elementos_cur.cantidad;
    #                 -- PRODUCTOS CON STOCK CON IGUAL GENERICO
    #
    #                 FOR _genericos_cur IN
    #                 SELECT t.id, t.product_tmpl_id, t.uom_id, t.numero, t.vencimiento, t.cantidad
    #                 FROM (
    #                     SELECT p.id, p.product_tmpl_id, pt.uom_id,'SIN LOTE' AS numero, NOW() as vencimiento,
    #                         sum(sq.qty) as cantidad
    #                     FROM product_product p
    #                     INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
    #                     INNER JOIN stock_quant sq on sq.product_id = p.id
    #                     LEFT JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
    #                     WHERE sq.location_id = _location_stock_id
    #                         AND pt.principio_activo_id = _elementos_cur.principio_activo_id
    #                         AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
    #                         AND pt.concentracion_valor = _elementos_cur.concentracion_valor
    #                         AND pt.concentracion_valor = _elementos_cur.concentracion_valor
    #                         AND sq.qty > 0
    #                         AND l.product_id IS NULL
    #                         AND sq.reservation_id IS NULL
    #                         AND pt.categoria_id = _sector_farmacia_id
    #                     GROUP BY p.id, pt.uom_id, l.name, l.life_date
    #
    #
    #                     UNION ALL
    #
    #                     SELECT p.id, p.product_tmpl_id, pt.uom_id, l.name as numero, l.life_date as vencimiento,
    #                         sum(sq.qty) as cantidad
    #                     FROM product_product p
    #                     INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
    #                     INNER JOIN stock_quant sq on sq.product_id = p.id
    #                     INNER JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
    #
    #                     WHERE sq.location_id = _location_stock_id
    #                         AND pt.principio_activo_id = _elementos_cur.principio_activo_id
    #                         AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
    #                         AND pt.concentracion_valor = _elementos_cur.concentracion_valor
    #                         AND pt.concentracion_valor = _elementos_cur.concentracion_valor
    #                         AND sq.qty > 0
    #                         AND sq.reservation_id IS NULL
    #                         AND pt.categoria_id = _sector_farmacia_id
    #
    #                     GROUP BY p.id, pt.uom_id, l.name, l.life_date
    #
    #
    #                 ) AS t
    #                 ORDER BY t.vencimiento
    #
    #                 LOOP
    #
    #                     -- verificar si hay stock --------------------------------------------------------------------------------------------
    #                     IF _cantidad > _genericos_cur.cantidad THEN
    #
    #                         -- no alcanza el stock, insertar este producto --
    #                         INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
    #                         VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
    #                             _genericos_cur.vencimiento, genericos_cur.cantidad);
    #
    #                         _cantidad := _cantidad - genericos_cur.cantidad;
    #
    #                     ELSE
    #
    #                         -- alcanza el stock, insertar este producto y pasar al siguiente --
    #                         INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
    #                         VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
    #                             _genericos_cur.vencimiento, _cantidad);
    #
    #                         _cantidad := 0;
    #
    #                         exit;
    #
    #                     END IF;
    #
    #
    #                 END LOOP;
    #
    #                 IF _cantidad > 0 THEN
    #
    #                     -- no alcanzo, insertar el producto original con el saldo --
    #                     INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
    #                     VALUES(_elementos_cur.product_id, _elementos_cur.product_tmpl_id, _elementos_cur.uom_id, NULL,
    #                         NULL, _cantidad);
    #
    #                 END IF;
    #
    #             END LOOP;
    #
    #             return query select * from tmp_productos;
    #
    #
    #             -- Error Handle --------------------------------------------------------------------------------------------
    #
    #             exception
    #             when others then
    #             GET STACKED DIAGNOSTICS _err_context = PG_EXCEPTION_CONTEXT;
    #             RAISE INFO 'Error Name:%',SQLERRM;
    #             RAISE INFO 'Error State:%', SQLSTATE;
    #             RAISE INFO 'Error Context:%', _err_context;
    #             return query select * from tmp_productos where 1=2;
    #
    #
    #         END;
    #         $BODY$
    #           LANGUAGE plpgsql VOLATILE
    #           COST 100
    #           ROWS 1000;
    #         ALTER FUNCTION sp_reponer(integer, integer, character varying, character varying)
    #           OWNER TO odoo
    #
    #     """)

    @api.multi
    def action_planilla(self):
        # Creo el libro Excel
        wb = Workbook(encoding='utf-8')
        ws = wb.add_sheet('Sheet 1', cell_overwrite_ok=True)

        # Estilos
        title_big = easyxf('font: name Arial, bold True; alignment: horizontal center;font:height 300;')
        header = easyxf('font: name Calibri, bold True; alignment: horizontal center;')
        """
        title = easyxf('font: name Calibri, bold True; alignment: horizontal left')
        title_number = easyxf('font: name Calibri, bold True; alignment: horizontal right',
                              num_format_str='#,##0.00;-#,##0.00;')
        numero_editable = easyxf('font: name Calibri; alignment: horizontal right; protection: cell_locked false;',
                                 num_format_str='#,##0.00;-#,##0.00;')
        numero_editable_bold = easyxf(
            'font: name Calibri, bold True; alignment: horizontal right; protection: cell_locked false;',
            num_format_str='#,##0.00;-#,##0.00;')
        integer = easyxf('font: name Calibri; alignment: horizontal left')
        fecha = easyxf('font: name Calibri; alignment: horizontal center', num_format_str='DD/MM/YYYY')
        totales = easyxf('font: name Calibri,bold True;')
        bold_fecha = easyxf('font: name Calibri, bold True; alignment: horizontal center',
                            num_format_str='DD/MM/YYYY')
        """

        fila = 0

        # Datos de la empresa y fecha de emision
        # ws.row(fila).height = 2 * 200
        # ws.write_merge(fila, fila, 3, 7, self.descripcion, title_big)

        fila += 1

        fuente = Font()
        fuente.name = "Calibri"
        estilo = XFStyle()
        estilo.font = fuente

        # Escribo el titulo de cada columna
        # La última columna es para el color
        # titulos = [descrip[0] for descrip in self.env.cr.description][:-1]
        #
        # for i, titulo in enumerate(titulos):
        #     ws.write(fila, i, titulo, header)


        for linea in self.move_lines:
            #
            #
            #
            ws.write(fila, 0, linea.product_id.display_name, estilo)
            ws.write(fila, 1, linea.product_qty, estilo)
            ws.write(fila, 2, linea.lote, estilo)
            fila += 1

        # Ajustar el ancho de las columnas
        anchos = {
            0: 34,
            1: 10,
            2: 20,

        }

        for col in range(0, 3):
            ws.col(col).width = anchos.get(col, 7) * 367

        # Armo el retorno
        fp = StringIO()
        wb.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data_to_save = base64.encodestring(data)

        # Nombre para el archivo
        self.write({
            'archivo_nombre': "Compras.xlsx",
            'archivo_contenido': data_to_save
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=stock.picking&field=archivo_contenido&id=%s&filename=%s' % (
                self.id,
                self.archivo_nombre,
            ),
            'target': 'self',
        }


StockPicking()
