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

    'name': 'AMSJ Cancelar ordenes de compra automáticas',
    'version': '1.0',
    'sequence': 1,
    'summary': '',
    'description': """
    AMSJ - cancelar ordenes de compra mas 30 dias
    
      
    """,
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'depends': ['base','purchase','dtm_amsj_stock_critico'],
    'data': [

             "views/cron.xml",

             
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
