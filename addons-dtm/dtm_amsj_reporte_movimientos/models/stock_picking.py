import math
import datetime
from openerp import api, models, fields


class StockPickingExtend(models.Model):

    _inherit = 'stock.picking'
    # _name = 'dtm_amsj_stock_picking_inherited'

    @api.multi
    def imprimir_etiquetas(self):
        sql = """
        SELECT sp.id, sq.qty, p.name_template, l.name, COALESCE(l.life_date,now() at time zone 'UYT')::date as life_date
        FROM stock_picking sp
        INNER JOIN stock_move sm on sm.picking_id = sp.id
        INNER JOIN stock_quant_move_rel smr on smr.move_id = sm.id
        INNER JOIN stock_quant sq on sq.id = smr.quant_id
        INNER JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
        INNER JOIN product_product p on p.id = sq.product_id
        INNER JOIN product_template pt on pt.id = p.product_tmpl_id
        WHERE sp.id = %(stock_picking_id)s
        """

        """
        for line in self.move_lines:
            for stock_quant_move_rel in line:
                import ipdb; ipdb.set_trace()
                print stock_quant_move_rel
        """

        self.env.cr.execute(sql, {'stock_picking_id': self.id })
        resultados = self.env.cr.fetchall()

        separado = []
        # id, cantidad, nombre, nombre_lote, fecha_vencimiento
        for resultado in resultados:
            fecha = resultado[4]
            fecha = datetime.datetime.strptime(fecha, '%Y-%m-%d').strftime('%d/%m/%Y')

            for x in range(0, int(math.ceil(resultado[1] / 10))):
                separado.append((
                    # resultado[0],
                    resultado[2],
                    resultado[3],
                    fecha,
                ))

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'dtm_amsj_reporte_movimientos.reporte_movimientos',
            'datas': { 'separado': separado },
            'model': 'dtm_amsj_reporte_movimientos.reporte_stock_movimientos'
        }
