import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
from openerp.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from openerp import models, fields, api
from openerp.modules import get_module_path
from openerp.exceptions import ValidationError
from cStringIO import StringIO
import time


class wizard_vista_dinamica(models.TransientModel):
    _name = "wizard.vista.dinamica"

    location_id = fields.Many2one('stock.location', 'Ubicacion', required=True)
    fecha_desde = fields.Date('Fecha desde', default=date.today(), required=True)
    fecha_hasta = fields.Date('Fecha hasta', default=date.today(), required=True)
    categoria_id = fields.Many2one('categoria', u'Sector', required=True)
    # forma_de_compra_id = fields.Many2one('forma.de.compra', 'Tipo de compra', default=0)

    @api.multi
    def carga_vista_dinamica(self):

        # view_pivot_id = self.env.ref('dtm_amsj_vista_dinamica_productos.view_vista_dinamica_productos_').id
        # domain = [('od_despatch_date','>=',self.date_from),('od_despatch_date','<=',self.date_to)]

        # select * from sp_consumo_rango_fechas('2019-12-01','2019-12-31',439,0,19)

        # import ipdb; ipdb.set_trace()  # breakpoint 64b76c87 //
        self.env.cr.execute(
            """
                SELECT *
                FROM  public.sp_consumo_rango_fechas(
                        %(fecha_desde)s,%(fecha_hasta)s,%(location_id)s,
                        %(tipo_compra)s,%(sector)s);

            """,
            {'location_id': self.location_id.id,
             'fecha_desde': self.fecha_desde,
             'fecha_hasta': self.fecha_hasta,
             'tipo_compra': 0,
             'sector': self.categoria_id.id})

        resultado = self.env.cr.fetchall()
        self.env.cr.execute('DELETE FROM dtm_amsj_informe_consumos_dinamico')

        if resultado:

            # self.env.cr.execute('DELETE FROM dtm_amsj_informe_consumos_dinamico')
            # self.env["dtm.amsj.informe.consumos.dinamico"].search([]).unlink()


            for i in resultado:


                # (u'35455', u'ACICLOVIR CREMA 5% * 5 GR.', 2.0, u'Physical Locations / SJM / Farmacia', u'Physical Locations / PCU / Existencias')

                sql='''INSERT INTO dtm_amsj_informe_consumos_dinamico(codigo, producto, cantidad, origen, destino, fecha) 
                                            VALUES(%(codigo)s, %(producto)s, %(cantidad)s, %(origen)s, %(destino)s, %(fecha)s);'''


                fecha_format=i[0]+'-01'
                fecha_aux = time.strptime(fecha_format,DEFAULT_SERVER_DATE_FORMAT)
                fecha_sql = time.strftime('%Y-%m-%d', fecha_aux)


                parametros = {
                             'codigo':i[1],
                             'producto':i[2],
                             'cantidad':i[3],
                             'origen':i[4],
                             'destino':i[5],
                             'fecha':fecha_sql,}

                # import ipdb; ipdb.set_trace()  # breakpoint 64b76c87 //
                self.env.cr.execute(sql,parametros)




        return {
            'name':'Productos',
            'type': 'ir.actions.act_window',
            'res_model': 'dtm.amsj.informe.consumos.dinamico',
            'view_type': 'form',
            'view_mode': 'graph',
            'res_id': False,
            'target': 'self',
            }

        # return {
        #         'name': _('test'),
        #         'view_type': 'tree',
        #         'view_mode': 'tree',
        #         'view_id': self.env.ref('account.invoice_tree').id,
        #         'res_model': 'account.invoice',
        #         'context': "{'type':'out_invoice'}",
        #         'type': 'ir.actions.act_window',
        #         'target': 'new',
        #       }


    # @api.model
    # def default_get(self, fields):
    #     rec = super(WizardModel, self).default_get(fields)
    #     active_model_id = self.env['order.line.model'].browse(self._context.get('active_id'))
    #     rec['wizard_field'] = active_model_id.active_model_field
    #     return rec