# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    tax_calculation_rounding = fields.Float('Unidad de redondeo de impuestos')
    tax_calculation_rounding_account_id = fields.Many2one(
        'account.account',
        'Cuenta de redondeo de impuestos',
        domain=[('type', '<>', 'view')])
    tax_calculation_rounding_method = fields.Selection(
        [('round_per_line', u'Redondeo por línea'),
         ('round_globally', 'Redondeo global'),
         ('swedish_round_globally', 'Redondeo global sueco'),
         ('swedish_add_invoice_line', u'Redonde Sueco agregando una línea'),
         ],
        string=u'Método de Cálculo de redondeo',
        help=u"Si selecciona 'Redondeo por línea': Por cada impuesto, su valor será calculado, redondeado y sumado."
             u"Si selecciona 'Redondeo global': Por cada impuesto, su valor será calculado y sumado, luego si corresponde redondeado."
             u"Si vende con impuestos incluidos debería seleccionar 'Redondeo por línea'")

