# -*- coding: utf-8 -*-

{
    'name': 'Pedidos - Por Consumos Sueros AMSJ',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    "category": "Sales",
    "depends": ['base', 'product','dtm_amsj_codigueras','dtm_amsj_seguridad','stock','dtm_amsj_stock_critico','dtm_amsj_agenda_pedidos_semanales'],
    'data': [
            'wizard/wizard.xml',
            # 'views/move.xml',
        ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
}
