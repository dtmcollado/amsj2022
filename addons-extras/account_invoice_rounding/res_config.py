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


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    tax_calculation_rounding = fields.Float(
        related='company_id.tax_calculation_rounding',
        string='Unidad de redondeo de impuestos',
        default=0.05)
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

    tax_calculation_rounding_account_id = fields.Many2one(
        related='company_id.tax_calculation_rounding_account_id',
        comodel='account.account',
        string='Cuenta de redondeo de impuestos',
        domain=[('type', '<>', 'view')])

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = super(AccountConfigSettings, self
                    ).onchange_company_id(cr, uid, ids,
                                          company_id, context=context)
        company = self.pool.get('res.company').browse(cr, uid, company_id,
                                                      context=context)
        res['value'][
            'tax_calculation_rounding'] = company.tax_calculation_rounding
        res['value']['tax_calculation_rounding_account_id'] = \
            company.tax_calculation_rounding_account_id.id
        return res
