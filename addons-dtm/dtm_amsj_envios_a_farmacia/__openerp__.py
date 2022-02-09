# -*- coding: utf-8 -*-

{
    'name': 'Envios a farmacias desde sectores',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'description': """
    
    """,        
    "category": "Sales",
    "depends": ['base', 'product','dtm_amsj_codigueras',
                'dtm_amsj_seguridad','stock','warehouse_stock_restrictions'],
    'data': [
        'wizard/wizard.xml',

    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
}
