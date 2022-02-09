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

import locale
import time
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT

def currency_fmt(value):
    # Establecer la localización por defecto
    locale.setlocale(locale.LC_ALL, '')

    # Retornar formateado
    if value is None:
        return locale.format('%10.2f', 0, grouping=True)
    else:
        return locale.format('%10.2f', value, grouping=True)


def date_fmt(fecha):
    if not fecha:
        return ""
    fecha = time.strptime(fecha, DEFAULT_SERVER_DATE_FORMAT)
    return "%02d/%02d/%4d" % (fecha.tm_mday, fecha.tm_mon, fecha.tm_year)
