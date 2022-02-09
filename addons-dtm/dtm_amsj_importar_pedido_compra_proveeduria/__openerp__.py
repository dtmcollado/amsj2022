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

    'name': 'AMSJ Importar pedido de compras centralizadas para proveeduria',
    'version': '1.0',
    'sequence': 4,
    'summary': '',
    'description': """
    Importación de pedidos de compra desde archivo CSV
    
    Se generan las ordenes de compra a partir de archivo CSV (comma separated values).
    El archivo contiene los datos de: producto y cantidad.
    
    #PC2 - Compras Centralizadas para proveeduria
         
    """,
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'depends': ['base','account'],
    'data': [
             "importa_csv.xml",
              'compras_importadas.xml',
             "views/compras_importadas_proveeduria.xml",
             "data/importaciones_centralizadas_proveeduria_sequence.xml",
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
