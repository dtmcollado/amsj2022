# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Datamatic (<http://www.datamatic.com.uy>).
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
{
    'name': 'Invoice line color dulplicate Products',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
     Módulo pinta de color las lineas de una factura que tengan productos repetidos.
    """,
    'author': 'Pedro',
    'maintainer': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'depends': ['account'],
    'data': ['dtm_amsj_invoice_line_color_view.xml'],
    'installable': True,
    'auto_install': False,
}
