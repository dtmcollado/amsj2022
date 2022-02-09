# -*- encoding: utf-8 -*-
##########################################################################
#    Copyright (C) OpenERP Uruguay (<http://openerp.com.uy>).
#    All Rights Reserved
# Credits######################################################
#    Coded by: Felipe Ferreira
#    Planified by: Felipe Ferreira
#    Finance by: Datamatic S.A. - www.datamatic.com.uy
#
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
{
    'name': 'Nombre Fantasia',
    'version': '1.0',
    'website' : 'www.datamatic.com.uy',
    'category': 'Personalización',
    'summary': 'Nombre Fantasia para Partners',
    'description': """
Nombre Fantasia para Partners
======================================

Este modulo permite  crea un campo para escribir el nombre fantasia de la empresamejorar los costos de proyectos a travez de la posibilidad de comparar costo estimados con 

""",
    'author': 'Felipe Ferreira',
    'depends': ['base'],
    'data': [
        'views/nombre_fantasia_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
