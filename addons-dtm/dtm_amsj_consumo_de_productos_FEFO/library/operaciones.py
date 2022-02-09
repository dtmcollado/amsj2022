# -*- encoding: utf-8 -*-
from operator import itemgetter
from openerp.exceptions import ValidationError, Warning


def validate_that_has_report_data():
    raise ValidationError(
        u"No se encuentran facturas a conformar para el período seleccionado")


def _datos_reporte(self):
    list_qweb = []
    dict_prov = {}

    consulta = """
           select  categoria_interna , destino ,
                   sum(total_fifo) ,
                   sum(total_ultima_compra)
           from consumos_report
           WHERE (fecha >= DATE %(ffecha_i)s and
                                fecha <= DATE %(ffecha_f)s)
                  """

    # filtros
    if self.sector_ids:
        consulta += """ and sector_id in %(sector_ids)s"""

    if self.categoria_ids:
        consulta += """ and categoria_interna_id in %(categoria_ids)s"""
    if self.origen_ids:
        consulta += """ and origen_id in %(origen_ids)s"""
    if self.destino_ids:
        consulta += """ and destino_id in %(destino_ids)s"""

    if not self.todos_FTM:
        if self.FTM:
            consulta += """ and FTM = 'True' """
        else:
            consulta += """ and FTM = 'False' """

    consulta += """ group by categoria_interna,destino 
                   order by categoria_interna,destino
                 """

    self.env.cr.execute(consulta,
                        {'ffecha_i': self.fecha_inicial,
                         'ffecha_f': self.fecha_final,
                         'sector_ids': tuple(self.sector_ids.ids),
                         'categoria_ids': tuple(self.categoria_ids.ids),
                         'origen_ids': tuple(self.origen_ids.ids),
                         'destino_ids': tuple(self.destino_ids.ids)
                         })

    resultado = self.env.cr.fetchall()
    #
    primero = True
    sub_total_fifo = 0
    sub_total_costo = 0
    total_fifo = 0
    total_costo = 0
    for tupla in resultado:

        if primero:
            cat = tupla[0]
            cat_ant = cat
            primero = False
        else:
            if cat_ant == tupla[0]:
                cat = ''
                sub_total_fifo += float(tupla[2])
                sub_total_costo += float(tupla[3])
            else:
                # me cambio categoria
                list_qweb.append(
                    {
                        'categoria': 'Sub total',
                        'origen': '',
                        'fifo': sub_total_fifo,
                        'compra': sub_total_costo,
                    })
                sub_total_fifo = 0
                sub_total_costo = 0
                cat = tupla[0]
                cat_ant = cat
        # Physical Locations
        if not tupla[2]:
            fifo = 0
        else:
            total_fifo += float(tupla[2])
            fifo = tupla[2]

        if not tupla[3]:
            costo = 0
        else:
            total_costo += float(tupla[3])
            costo = tupla[3]

        list_qweb.append(
            {
                'categoria': cat,
                'origen': tupla[1],
                'fifo': fifo,
                'compra': costo,
            })

    x = 1

    list_qweb.append(
        {
            'categoria': 'Sub total',
            'origen': '',
            'fifo': sub_total_fifo,
            'compra': sub_total_costo,
        })

    list_qweb.append(
        {
            'categoria': 'Totales',
            'origen': '',
            'fifo': total_fifo,
            'compra': total_costo,
        })
    return list_qweb
