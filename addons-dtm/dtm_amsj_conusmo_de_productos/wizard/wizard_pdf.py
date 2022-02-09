# -*- encoding: utf-8 -*-

import base64
import xlwt
from cStringIO import StringIO
from datetime import date
from xlsxwriter.workbook import Workbook
from xlwt import Workbook, XFStyle, easyxf, Formula, Font

from dateutil.relativedelta import relativedelta
import datetime
from openerp import models, fields, api
from openerp.exceptions import ValidationError
from ..library import operaciones as report_ops
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT


class wizardPDF(models.TransientModel):
    _name = "wizard.pdf"

    @api.multi
    def get_domain_sector(self):
        # 18
        # 19
        return [('id', '<>', 22)]

    fecha_inicial = fields.Date('Begin date', default=date.today().replace(day=1))
    fecha_final = fields.Date('End date', default=date.today())

    # sector_id = fields.Many2one('categoria', 'Sector')
    sector_ids = fields.Many2one(comodel_name='categoria',
                                  string="Sector", domain=get_domain_sector
                                  )

    # categoria = fields.Many2one('product.category', 'Categoria')
    categoria_ids = fields.Many2many(comodel_name='product.category',
                                     string="Categorias"
                                     )

    date = fields.Date(string='Fecha',
                       index=True, copy=False, default=date.today(), required=True)

    categoria_todos = fields.Boolean('Todas las Categorias', default=False)
    sector_todos = fields.Boolean('Todos los Sectores', default=False)

    archivo_nombre = fields.Char(string='Nombre del archivo')
    archivo_contenido = fields.Binary(string="Archivo")

    todos_FTM = fields.Boolean('FTM Todos', default=True)

    almacen_origen_ids = fields.Many2one(comodel_name='stock.warehouse', string='Almacenes')
    origen_ids = fields.Many2many(comodel_name='stock.location',
                                  string="Ubicaciónes", compute='_compute_location_origen', readonly=False)

    almacen_destino_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_user', 'user_id', 'warehouse_id',
                                           string='Almacenes')

    destino_ids = fields.Many2many('stock.location', 'stock_location_user', 'user_id', 'location_id',
                                   compute='_compute_location_destino', string="Ubicaciónes", readonly=False)

    FTM = fields.Boolean('FTM', default=False)
    centro_costo = fields.Char(string='Centro de Costo')

    @api.one
    @api.depends('almacen_origen_ids')
    def _compute_location_origen(self):
        location_ids = []

        if self.almacen_origen_ids:
            for w in self.almacen_origen_ids:
                for loc in w.view_location_id.child_ids:
                    if not loc.scrap_location:
                        location_ids.append(loc.id)
                    for loc1 in loc.child_ids:
                        if not loc1.scrap_location:
                            location_ids.append(loc1.id)
                        for loc2 in loc1.child_ids:
                            if not loc2.scrap_location:
                                location_ids.append(loc2.id)
                            for loc3 in loc2.child_ids:
                                if not loc3.scrap_location:
                                    location_ids.append(loc3.id)
        #
        if location_ids:
            self.origen_ids = location_ids

    @api.one
    @api.depends('almacen_destino_ids')
    def _compute_location_destino(self):
        location_ids = []

        if self.almacen_destino_ids:
            for w in self.almacen_destino_ids:
                for loc in w.view_location_id.child_ids:
                    if loc.scrap_location:
                        location_ids.append(loc.id)
                    for loc1 in loc.child_ids:
                        if loc1.scrap_location:
                            location_ids.append(loc1.id)
                        for loc2 in loc1.child_ids:
                            if loc2.scrap_location:
                                location_ids.append(loc2.id)
                                for loc3 in loc2.child_ids:
                                    if not loc3.scrap_location:
                                        location_ids.append(loc3.id)

        if location_ids:
            self.destino_ids = location_ids

    # @api.one
    # @api.constrains('fecha_desde', 'fecha_hasta')
    # def _control_fechas(self):
    #     if self.fecha_inicial > self.fecha_final:
    #         raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")


    # pdf de compras , ok junio 2021
    @api.multi
    def action_report(self):
        self.ensure_one()

        data = {}
        data['ids'] = self._context.get('active_ids', [])
        data['model'] = self._context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read()
        data['lineas'] = report_ops._datos_reporte(self)

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'dtm_amsj_conusmo_de_productos.invoices_conformar',
            'report_title': 'Consumos',
            'datas': data,
        }




wizardPDF()
