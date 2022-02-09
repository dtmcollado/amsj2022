# -*- coding: utf-8 -*-

{
    'name': 'Prestamos',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'description': """
    
    """,        
    "category": "",
    "depends": ['base', 'product','dtm_amsj_codigueras',
                'dtm_amsj_seguridad','stock','warehouse_stock_restrictions'],
    'data': [
        'wizard/wizard_prestamos.xml',
        'wizard/wizard_de_terceros.xml',
        'wizard/wizard_dev.xml',
        'views/move.xml',
        'views/report_remito_prestamo.xml'

    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
}
