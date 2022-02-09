# -*- coding: utf-8 -*-
# from datetime import date, timedelta, time, datetime


import logging
from datetime import date, datetime,timedelta

from openerp import models, fields, api
from openerp.exceptions import ValidationError

from ..library import formatters

_logger = logging.getLogger(__name__)


class dtm_amsj_informe_ventas_contado(models.TransientModel):
    _name = "dtm_amsj_informe_ventas_contado"

    date_from = fields.Datetime('Fecha desde', required=True, default=fields.datetime.now().replace(day=1))
    date_to = fields.Datetime('Fecha hasta', required=True, default=fields.datetime.now())
    location_id = fields.Many2one(comodel_name='stock.location', string=u'Ubicación', required=True,
                                  domain=[('ventas_contado', '=', True)])

    total_general = float()

    def validate_that_has_report_data(self):
        raise ValidationError(
            u"No se encontraron datos a mostrar para el período y ubicación seleccionada")

    def _datos_reporte(self):
        list_qweb = []
        date_from = datetime.strptime(self.date_from, "%Y-%m-%d %H:%M:%S")
       # date_from  = date_from- timedelta(hours=3)
        date_to = datetime.strptime(self.date_to, "%Y-%m-%d %H:%M:%S")
        #date_to  = date_to- timedelta(hours=3)

        consulta = """ select price_unit, sum(product_qty), product_id, sum(product_qty * price_unit) as total
        from stock_move where state = 'done' and location_dest_id = %s and create_date >= %s and create_date <= %s
         group by product_id , price_unit
         
        """

        self.env.cr.execute(consulta, (self.location_id.id, date_from, date_to,))

        resultado = self.env.cr.fetchall()
        for tupla in resultado:
            product_id = self.env['product.product'].browse(tupla[2])
            default_code = product_id.default_code
            cantidad = tupla[1] or float()
            costo = tupla[0] or float()
            if tupla[0]:
                total = tupla[0] * tupla[1]
            else:
                total = product_id.standard_price * tupla[1]

            if costo == 0:
                costo = product_id.standard_price
                total = product_id.standard_price * tupla[1]

            self.total_general += total
            

            list_qweb.append(
                {
                    'date':'',
                    'codigo': default_code,
                    'producto': product_id.name_template,
                    'costo': round(costo, 2),
                    'cantidad': round(cantidad, 2),
                    'total': round(total, 2),

                })
        if len(list_qweb) == 0:
            self.validate_that_has_report_data()
        return list_qweb

    @api.multi
    def action_report(self):
        self.ensure_one()
        now = datetime.now()
        # print()
        salida = formatters.current_date_format(now)

        fecha = 'San José de Mayo, ' + salida + '.'

        data = {}
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read()
        data['lineas'] = self._datos_reporte()
        data['total_stock'] = round(self.total_general, 2)
        data['report_title'] = fecha

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'dtm_amsj_informe_ventas_contado.informe_ventas_contado',
            'datas': data,
        }


dtm_amsj_informe_ventas_contado()
