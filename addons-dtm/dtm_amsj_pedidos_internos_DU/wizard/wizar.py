# -*- encoding: utf-8 -*-

from datetime import date, timedelta, datetime
from openerp.exceptions import ValidationError
from openerp import models, fields, api, tools

CREATE = lambda values: (0, False, values)
UPDATE = lambda id, values: (1, id, values)
DELETE = lambda id: (2, id, False)
FORGET = lambda id: (3, id, False)
LINK_TO = lambda id: (4, id, False)
DELETE_ALL = lambda: (5, False, False)
REPLACE_WITH = lambda ids: (6, False, ids)


class wizline(models.TransientModel):
    _name = "wizard.pedido.consumo.interno.du.du.line"

    product_id = fields.Many2one('product.product', 'Product', required=True, select=True)
    product_qty = fields.Float('Quantity', help='Quantity in the default UoM of the product')
    transf_id = fields.Many2one('wizard.pedido.consumo.interno.du')


class wizard(models.TransientModel):
    _name = "wizard.pedido.consumo.interno.du"

    @api.multi
    def get_domain_orig(self):
        user = self.env["res.users"].browse([self.env.uid])
        picking_type_ids = user.default_picking_type_ids

        id = False
        if len(picking_type_ids) == 1:
            dest_id = picking_type_ids.default_location_dest_id
            if len(dest_id) == 1:
                self.new_location_orig_id = dest_id.id
        else:
            for t in picking_type_ids:
                if t.code == u'internal':
                    id = t.default_location_dest_id.id

        return [('id', '=', id)]

    @api.multi
    def get_domain_dest(self):

        user = self.env["res.users"].browse([self.env.uid])
        sin_sector = []

        for location in user.stock_location_ids:
            if not location.sector.id:
                if location.usage == 'internal':
                    sin_sector.append(location.id)

        location_ids = sin_sector[:]  # list.copy se agregó en python 3.3

        return [('id', '=', location_ids)]

    # @api.model
    # def _default_date(self):
    #     return datetime.today() - timedelta(days=7)

    def _default_sector(self):
        return 17

    location_dest_readonly = fields.Boolean()

    new_location_orig_id = fields.Many2one('stock.location', domain=get_domain_orig)
    new_location_dest_id = fields.Many2one('stock.location', domain=get_domain_dest)

    fecha_inicial = fields.Datetime('Begin date')
    fecha_final = fields.Datetime('End date')

    sector_ids = fields.Many2one('categoria', string="Sector", default=_default_sector)

    move_lines = fields.One2many('wizard.pedido.consumo.interno.du.du.line', inverse_name='transf_id',
                                 String='Internal Moves', copy=True)

    cantidad = fields.Integer('cantidad')
    log = fields.Html('No encontrados')

    @api.one
    @api.constrains('fecha_inicial', 'fecha_final')
    def _control_fechas(self):
        if self.fecha_inicial >= self.fecha_final:
            raise ValidationError("El valor de la fecha 'Inicial' debe ser menor a la fecha 'Final'")

    def formato_fecha(self, fecha, dias_a_agregar=0):
        fecha = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
        if dias_a_agregar:
            fecha = fecha + timedelta(days=dias_a_agregar)
            fecha2 = fecha.strftime('%d/%m/%Y %H:%M:%S')
        return fecha2

    # PARA SQLSERVER
    @api.multi
    def action_lista_productos(self):
        sector_amsj = self.new_location_dest_id.sector_amsj or '0'
        subsector_amsj = self.new_location_dest_id.subsector_amsj or '0'
        sucursal_amsj = self.new_location_dest_id.sucursal_amsj or '0'

        fecha_desde = self.fecha_inicial
        fecha_hasta = self.fecha_final

        sector_id = self.sector_ids.id

        fecha_i = self.fecha_inicial
        fecha_f = self.fecha_final

        sql = """select  
                   CONVERT(varchar,[Código Geosalud]) as codigo_geosalud,
                   CONVERT(varchar,[Cantidad]) as cantidad,CONVERT(varchar,[Nombre Medicamento])  as nombre ,
                   CONVERT(varchar,[Codigo Unidad de Medida]) as unidad_medida
                       from CONSUMOS_GEOSALUD 
                   where         
                    CONVERT(varchar,[Número Sector]) ='%s' and
                    CONVERT(varchar,[Número Subsector]) ='%s' and
                    [Fecha de Consumo] >= CONVERT(datetime,'%s',120) and
                    [Fecha de Consumo] < CONVERT(datetime,'%s',120) and
                     CONVERT(varchar,[Número de Expendio]) ='%s'""" % (
            sector_amsj, subsector_amsj, fecha_desde, fecha_hasta, sucursal_amsj)

        SERV = self.pool.get('connector.sqlserver').search(self._cr, self._uid, [('name', '=', "amsj")])
        servidor_SQL = self.pool.get('connector.sqlserver').browse(self._cr, self._uid, SERV, self._context)
        conn = servidor_SQL.connect()
        if conn:
            cursor = servidor_SQL.getNewCursor(conn)
            cursor.execute(sql)

            prods = dict()
            lineas = list()
            self.log = " "
            row = cursor.fetchone()

            while row:

                codigo_geosalud = row[0]
                cantidad_linea = float(row[1])
                productos = self.env['product.product'].search([
                    ('codigo_geosalud', '=', codigo_geosalud),
                    ('categoria_id', '=', self.sector_ids.id),
                    ('tipo_de_empaque','=', 2)
                   ])
                if not productos:
                    self.cantidad += 1
                    if codigo_geosalud:
                        self.log += '<p> Codigo Geosalud: ' + str(row[0]) + ' - ' + str(row[2]) + '</p>'
                for producto in productos:
                    if not prods.get(codigo_geosalud):
                        prods[codigo_geosalud] = {
                            'product_id': producto.id,
                            'product_qty': cantidad_linea,
                        }
                    else:
                        cantidad = float(prods[codigo_geosalud]['product_qty']) + cantidad_linea
                        prods[codigo_geosalud] = {
                            'product_id': producto.id,
                            'product_qty': cantidad,
                        }
                row = cursor.fetchone()

            for prod in prods.values():
                linea = self.env['wizard.pedido.consumo.interno.du.du.line'].create(prod)
                lineas.append(linea)

            self.write({'move_lines': [(6, 0, [linea.id for linea in lineas])]})
            self.move_lines = [(6, 0, [linea.id for linea in lineas])]
            conn.commit()
            conn.close

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.pedido.consumo.interno.du',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_create_picking_interno(self):
        ubicacion_destino = self.new_location_dest_id
        almacen = ubicacion_destino.almacen_id
        ubicacion_origen = self.env['stock.location'].search([('almacen_id', '=', almacen.id),
                                                              ('principal_del_expendio', '=', True)], limit=1)

        if ubicacion_origen.id == ubicacion_destino.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": u"Origen y Destino deben de ser diferentes. Verifique la ubicación principal del almacén.",
                    "sticky": True,
                }
            }

        picking_out = self.env['stock.picking'].create({
            "location_id": ubicacion_origen.id,
            'location_dest_id': ubicacion_destino.id,
            'picking_type_id': almacen.int_type_id.id,
        })

        for line in self.move_lines:
            self.env['stock.move'].create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking_out.id,
                'location_id': ubicacion_origen.id,
                'location_dest_id': ubicacion_destino.id,
                'state': "confirmed",
            })

        if not self.move_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'action_warn',
                'name': 'Notificación',
                'params': {
                    "title": "Transferencia",
                    "text": "No se encontraron productos para generar transferencia.",
                    "sticky": True,
                }
            }
        else:
            # actualizo fecha ultima reposicion
            hoy = datetime.today()
            ubicacion_destino.write({'fecha_ultima_reposicion': hoy})


wizard()
