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

from openerp import api, models
from ..library import formatters
from datetime import datetime

class ParticularReport(models.AbstractModel):
    _inherit = 'report.abstract_report'
    _name = 'report.dtm_amsj_informe_ventas_contado.informe_ventas_contado'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']

        report = report_obj._get_report_from_name('dtm_amsj_informe_ventas_contado.informe_ventas_contado')

        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'lineas': data['lineas'],
            'currency_fmt': formatters.currency_fmt,
            'report_title': data['report_title'],
            'total_stock': data['total_stock'],

        }
        return report_obj.render('dtm_amsj_informe_ventas_contado.informe_ventas_contado', docargs)


ParticularReport()
