stock_maximo_id = self.env['ubicacion.stockcritico'].search(
                    [('ubicacion_id', '=', record.new_location_dest_id.id),
                     ('product_tmpl_id', '=', product_template_id)
                     ], limit=1)



