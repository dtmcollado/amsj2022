# -*- coding: utf-8 -*-

{
    'name': 'Registro Consumos',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'description': """
    
    """,        
    "category": "Sales",
    "depends": ['base', 'product','dtm_amsj_codigueras',
                'dtm_amsj_seguridad','stock','warehouse_stock_restrictions','dtm_amsj_conusmo_de_productos'],
    'data': [
        'wizard/wizard.xml',
        'wizard/wizard_anular.xml',

    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
}
