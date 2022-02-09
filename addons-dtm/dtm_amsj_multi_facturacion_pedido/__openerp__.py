# -*- coding: utf-8 -*-

{
    'name': 'Multi facturación de pedidos',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    "category": "purchases",
    "depends": ['base',
                'product',
                'purchase',
                'dtm_amsj_seguridad',
                'stock',
                'dtm_sql_server_connector',
                ],
    'data': ['views/multifacturacion_pedidos.xml'],
    'demo_xml': [],
    'installable': True,
    'application': True,
}

