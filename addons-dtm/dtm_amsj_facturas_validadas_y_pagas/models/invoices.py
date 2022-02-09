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
from openerp.exceptions import ValidationError
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

class dtm_amsj_account_invoice(models.Model):
    _inherit = 'account.invoice'

    date_invoice = fields.Date(string='Fecha de ingreso a contabilidad',
                               readonly=True, states={'draft': [('readonly', False)]}, index=True,
                               help="Keep empty to use the current date", copy=False)

    fecha_factura = fields.Date(string='Fecha Factura',
                               readonly=True, states={'draft': [('readonly', False)]}, index=True,copy=False)

    @api.one
    @api.constrains('date_invoice', 'fecha_factura')
    def _control_fechas(self):
        if self.date_invoice:
            if datetime.strptime(self.date_invoice, DEFAULT_SERVER_DATE_FORMAT) > datetime.today():
                raise ValidationError("El valor de la fecha  debe ser menor o igual a la fecha del dia")

        if self.fecha_factura:
            if datetime.strptime(self.fecha_factura, DEFAULT_SERVER_DATE_FORMAT) > datetime.today():
                raise ValidationError("El valor de la fecha  debe ser menor o igual a la fecha del dia")

        if self.fecha_factura and not self.date_invoice:
            self.date_invoice = self.fecha_factura

        #if not self.fecha_factura:
        #    raise ValidationError("Falta fecha ingresar fecha factura")

    @api.multi
    def factura_wizard(self):
        self.ensure_one()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            # 'view_id': form_id.id,
            'view_id': False,
            'res_model': 'account.invoice',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self.env.context,
        }

    # @api.one
    @api.multi
    @api.depends('date_invoice')
    def get_mes(self):
        for rec in self:
            if rec.date_invoice:
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
                    mes = meses.get(datetime.strptime(rec.date_invoice, '%Y-%m-%d %H:%M:%S').strftime('%m'))
                except:
                    mes = meses.get(datetime.strptime(rec.date_invoice, '%Y-%m-%d').strftime('%m'))
                rec.mes_calculado = mes
                rec.write({'mes': mes})

    # @api.one
    @api.multi
    @api.depends('date_invoice')
    def get_anio(self):
        for rec in self:
            if rec.date_invoice:
                try:
                    rec.anio_calculado = datetime.strptime(rec.date_invoice, '%Y-%m-%d %H:%M:%S').strftime('%Y')
                except:
                    rec.anio_calculado = datetime.strptime(rec.date_invoice, '%Y-%m-%d').strftime('%Y')
                rec.anio = rec.anio_calculado
                rec.write({'anio': rec.anio_calculado})

    mes_calculado = fields.Char(string='mes', compute='get_mes')
    mes = fields.Char(string='mes', store=True)
    anio_calculado = fields.Integer(string='mes', compute='get_anio')
    anio = fields.Integer(string=u'año', store=True)


dtm_amsj_account_invoice()





