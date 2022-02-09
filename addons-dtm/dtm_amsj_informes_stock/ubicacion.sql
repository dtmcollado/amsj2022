  SELECT replace(replace(sl.complete_name,'Physical Locations / ',''),'Ubicaciones físicas / ','')::character varying as Ubicacion,
                    p.default_code::character varying as codigo,
                    p.name_template::character varying as articulo,
                    t.despues,
                    t.total,
                    pc.name::character varying as categoria,
                    fa.name::character varying as Tipo_de_bien,
                    t.inventariado
                from sp_stock_history_fifo_ubicacion(%(fecha_balance)s,%(fecha_inicio)s, %(fecha_fin)s,%(param_ubic)s , %(param_prod)s , %(param_empaque)s,%(param_categ)s,%(param_invent)s,%(opciones_fecha)s) t
                INNER JOIN product_product p ON p.id = t.id_producto
                INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                INNER JOIN stock_location sl ON sl.id = t.id_ubicacion
                LEFT JOIN familia  fa ON  fa.id = pt.familia_id
                LEFT JOIN product_category pc on pc.id = pt.categ_id;