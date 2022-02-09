# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Gabriel Henao.
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
    "name": "Uruguay Localization Toponyms",
    "version": "1.0",
    "description": """
Uruguyan toponyms.

Incluye una lista de los Departamentos de Uruguay,
una lista de bancos y una lista de títulos/denominaciones de personas
físicas y jurídicas.

Sustituye a los módulos previos:
    l10n_uy_states
    l10n_uy_bank
    l10n_uy_partner_title

    """,
    "author": "Datamatic",
    "website": "http://datamatic.com.uy",
    "category": "Localization/Toponyms",
    "depends": [
			"base_state_ubication",
			],
	"data":[
        "l10n_uy_toponyms_data.xml",
			],
    "demo_xml": [
			],
    "update_xml": [
			],
    "active": False,
    "installable": True,
    "certificate" : "",
    "images": [ ],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
