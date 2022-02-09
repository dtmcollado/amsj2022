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

    'name': 'AMSJ Importar gastos COBOL',
    'version': '1.0',
    'sequence': 4,
    'summary': '',
    'description': """
    Importación gastos(cobol) desde archivo CSV
    
         
    """,
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'depends': ['base','account','dtm_amsj_stock_critico'],
    'data': [
             'security/ir.model.access.csv',
             'filiales.xml',
             'consumos_cobol.xml',
             'importa_csv.xml',
             'stock_picking.xml',
             # 'transferidos.xml',
             # "importa_csv_mensual.xml",
             # "views/compras_importadas.xml",
             # "views/compras_importadas_mensuales.xml",
             # "views/config_settings.xml",
             # "data/importaciones_centralizadas_sequence.xml",
             # "data/importaciones_mensuales_sequence.xml",
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
