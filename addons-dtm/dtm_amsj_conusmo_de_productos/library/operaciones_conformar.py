# -*- encoding: utf-8 -*-
from operator import itemgetter
from openerp.exceptions import ValidationError, Warning


def validate_that_has_report_data():
    raise ValidationError(
        u"No se encuentran facturas a conformar para el período seleccionado")


def _proveedor_obra(self):


    list_qweb = []



    dict_prov = {}


    consulta =  """
            SELECT 
                c.name as sector,
                t.name as categoria_interna,
                sum(m.product_qty),
	            l.complete_name as origen,
	            l2.complete_name as destino,
	            m.centro_costos
            FROM public.stock_move m
      INNER JOIN stock_location l ON l.id = m.location_id
      INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
      INNER JOIN product_product p ON p.id = m.product_id
      INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
      INNER JOIN product_category t ON t.id = pt.categ_id
      INNER JOIN categoria c ON c.id = pt.categoria_id """

    if self.sector_id:
        consulta +=  """WHERE l2.scrap_location = true and c.id = %(sector_id)s""" 
    else:
        consulta += """WHERE l2.scrap_location = true"""

    if self.categoria:
        consulta += """ and t.id = %(categoria_id)s"""

    consulta +=  """ GROUP BY c.name,t.name,l.complete_name,l2.complete_name, m.centro_costos;
        """



    self.env.cr.execute(consulta,
        {'ffecha_i': self.fecha_inicial,
         'ffecha_f': self.fecha_final,
         'sector_id': self.sector_id.id,
         'categoria_id': self.categoria.id
         })

    #  self.categoria.id
    #  self.sector_id.id

    resultado = self.env.cr.fetchall()
    #
    for tupla in resultado:
        list_qweb.append(
            {
                'sector': tupla[0],
                'categoria': tupla[1],
                'cantidad': tupla[2],
                'origen': tupla[3],
                'destino': tupla[4],
                'centro_costo': tupla[5],
            })

    return list_qweb

