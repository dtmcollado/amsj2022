# -*- coding: utf-8 -*-

{
    'name': 'Transferencia interna',
    'version': '1.0',
    'author': 'Datamatic',
    'website': 'http://www.datamatic.com.uy',
    'description': """
    Transferencia interna
    
    Registra transferencias internas entre dos ubicaciones.
         
    GA2 (Gestión de almacenes) Pedidos semanales
    """,        
    "category": "Sales",
    "depends": ['base', 'product','dtm_amsj_codigueras',
                'dtm_amsj_seguridad','stock',
                'warehouse_stock_restrictions','dtm_amsj_stock_critico'],
    'data': [
        'wizard/wizard_reposicion.xml',
        'wizard/wizard_transferencia_interna.xml',
        'wizard/wizard_transferencia_entre_expendios.xml'
    ],
    'demo_xml': [],
    'active': False,
    'installable': True,
    'application': True,
}
