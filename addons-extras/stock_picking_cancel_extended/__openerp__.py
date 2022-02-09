# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    "name": "Stock Picking Cancel/Reverse",
    'version': '8.0.0.3',
    "author": "BrowseInfo",
    "category": "Warehouse",
    "website": "http://www.browseinfo.in",
    'summary': 'This module helps to reverse the done picking, allow to cancel picking and set to draft',
    "depends": [
        "stock","sale_stock",
    ],
    "demo": [],
    'description': """
    -stock picking reverse workflow, stock picking cancel, delivery order cancel, incoming shipment cancel, cancel picking order, cancel delivery order, cancel incoming shipment, cancel order, set to draft picking, cancel done picking, revese picking process, cancel done delivery order.reverse delivery order.
    """,
    'price': '35.00',
    'currency': "EUR",
    "data": [
        "security/picking_security.xml",
        "stock_view.xml"
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,
}
