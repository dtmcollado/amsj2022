# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
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

from datetime import date
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import Warning
import logging


class dtm_amsj_seguridad_botones(models.Model):
    _inherit = 'stock.picking'
    es_usuario = fields.Boolean(string='Usuario', compute='usuario_creador')
    ultimo_cambio_btn_revertir=fields.Boolean(string='Usuario', compute='ultimo_cambio')
    grupo_pertenece = fields.Boolean(string='grupo', compute='filtro_grupo')

    @api.one
    @api.depends('es_usuario')
    def usuario_creador(self):
        grupo_farmacia = self.env['res.groups'].search([('name', '=', 'Farmacia')])
        usuarios_farmacia =[]
        if grupo_farmacia:
            usuarios_farmacia = [i.id for i in grupo_farmacia.users]
        if self.env.user.id in (usuarios_farmacia):
            if self.por_extraordinario and self.state not in ('done','cancel'):
                self.es_usuario = True
        else:
            self.es_usuario = (self.env.user.id == self.create_uid.id)
        # print self.es_usuario,'logueado', self.env.user.id, 'creado', self.create_uid.id


    @api.one
    @api.depends('ultimo_cambio_btn_revertir')
    def ultimo_cambio(self):
        self.ultimo_cambio_btn_revertir = (self.env.user.id == self.write_uid.id)
        # print self.ultimo_cambio_btn_revertir,'logueado', self.env.user.id, 'modificado x', self.write_uid.id



    @api.multi
    @api.depends('grupo_pertenece')
    def filtro_grupo(self):
        grupo_filial=self.env['res.groups'].search([('name','=','Filial')])
        usuarios_filial=False
        
        if grupo_filial:
            usuarios_filial=[i.id for i in grupo_filial.users]

        self.grupo_pertenece = (self.env.user.id in usuarios_filial)
        # print self.grupo_pertenece,'es filial'



# groups="dtm_amsj_seguridad.group_amsj_filial"










 


    
    






       




            






        
