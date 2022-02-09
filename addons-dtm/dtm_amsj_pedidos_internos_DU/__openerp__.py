# -*- coding: utf-8 -*-

{
    'name': 'Pedidos DU - Por Consumo Interno',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    "category": "Sales",
    "depends": ['base', 'product', 'dtm_amsj_codigueras', 'dtm_amsj_seguridad', 'stock','dtm_amsj_stock_critico'],
    'data': [
        'wizard/wizard.xml',
        # 'views/move.xml',
    ],
    'demo_xml': [],
    'active': False,
    'installable': False,
    'application': True,
}
