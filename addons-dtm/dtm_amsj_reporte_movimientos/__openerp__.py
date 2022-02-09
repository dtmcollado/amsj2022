# -*- coding: utf-8 -*-

{
    'name': 'Reporte movimientos',
    'version': '20180815',
    'author': 'Datamatic',
    'description': """
    """,    
    
    'website': 'http://www.datamatic.com.uy',
    "category": "Sales",
    "depends": [
        'base',
        'product',
        'dtm_amsj_codigueras',
        'stock',
        'mrp',
    ],
    'data': [
        'report/reporte.xml',
        'report/etiqueta_template.xml',
        'views/stock_picking.xml',
    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': False,
}
