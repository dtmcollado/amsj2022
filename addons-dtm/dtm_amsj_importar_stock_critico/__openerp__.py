# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 BrowseInfo(<http://www.browseinfo.in>).
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

    'name': 'AMSJ Importar Stock Crítico',
    'version': '1.0',
    'sequence': 4,
    'summary': '',
    'description': """
    Importación de Stock Crítico desde archivo CSV
    
      
    """,
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'depends': ['base','account'],
    'data': [
             "dtm_amsj_importar_stock_critico_wizard.xml",
             # "importa_csv_mensual.xml",
             
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
