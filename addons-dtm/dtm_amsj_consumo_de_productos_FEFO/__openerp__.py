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
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name':     u'Consumo de productos FEFO En desarrollo',
    'author':   'Datamatic',
    'website':  'http://www.datamatic.com.uy',
    'license':  'AGPL-3',
    'version':  '1.0',
    'description': u"""
DTM - Consumo de productos - AMSJ
==================================
En Almacen / Trazabilidad, se crea un menu que muestra el consumo de los productos (consumibles) y a qué precio.

""",
    'depends': [
        'base',
        'product',
        'stock',
        'dtm_amsj_seguridad',
        'dtm_amsj_productos'
    ],
    'data': [
        'views/stock_move_consumo_view.xml',
        'wizard/wizard.xml',
        'report/invoices_conformar.xml',
        'data/report.xml',
    ],
    'demo': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': True
}
