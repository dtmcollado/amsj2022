
CREATE OR REPLACE FUNCTION public.sp_stock_critico_DU(
    IN _location_id integer,
    IN _principio_activo_id integer,
    IN _forma_farmaceutica_id integer,
    IN _concentracion_valor numeric,
    IN _concentracion_unidad integer)
  RETURNS TABLE(location_id integer, principio_activo_id integer, forma_farmaceutica_id integer, concentracion_valor numeric, concentracion_unidad integer, stock_maximo numeric, stock_actual numeric) AS
$BODY$
            DECLARE


            -- Manejando el error --
            _err_context text;

            BEGIN

                return query
                SELECT l.ubicacion_id, pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad, sum(stock_critico)::numeric AS stock_maximo, sum(sq.qty)::numeric as stock_actual
		FROM ubicacion_stockcritico l
		INNER JOIN product_template pt ON pt.id = l.product_tmpl_id
		LEFT JOIN (
			SELECT sq.location_id, pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad, SUM(qty) as qty
			FROM stock_quant sq
			INNER JOIN product_product p ON p.id = sq.product_id
			INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
			INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque AND lower(te.name) like 'unitario'
			INNER JOIN principio_activo pa ON pa.id = pt.principio_activo_id
			GROUP BY sq.location_id, pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad
		) AS sq ON l.ubicacion_id = sq.location_id
			AND pt.principio_activo_id = sq.principio_activo_id
			AND pt.forma_farmaceutica_id = sq.forma_farmaceutica_id
			AND pt.concentracion_valor = sq.concentracion_valor
			AND pt.concentracion_unidad = sq.concentracion_unidad

		WHERE l.ubicacion_id = _location_id
			AND pt.principio_activo_id = _principio_activo_id
			AND pt.forma_farmaceutica_id = _forma_farmaceutica_id
			AND pt.concentracion_valor = _concentracion_valor
			AND pt.concentracion_unidad = _concentracion_unidad
			AND coalesce(pt.rmc,false) = false
		GROUP BY l.ubicacion_id, pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad;

            END;
  $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.sp_stock_critico(integer, integer, integer, numeric, integer)
  OWNER TO odoo;




CREATE OR REPLACE FUNCTION public.sp_reponer_du(
    IN _location_id integer,
    IN _location_stock_id integer,
    IN _fecha_desde character varying,
    IN _fecha_hasta character varying)
  RETURNS TABLE(product_id integer, product_tmpl_id integer, uom_id integer, lot_id character varying, life_date date, qty numeric, stock integer) AS
$BODY$
            DECLARE

            --crear una tabla temporal para ir insertando los productos que voy a elegir

            _elementos_cur record;
            _genericos_cur record;
            _sector_farmacia_id integer;
            _almacen integer;
            _cantidad numeric;
            _stock_maximo numeric;
            _stock_actual numeric;

            -- Manejando el error --
            _err_context text;

            BEGIN

                -- tabla temporal --
                DROP TABLE IF EXISTS tmp_productos;
                CREATE LOCAL TEMP TABLE tmp_productos
                 ( product_id integer,
                   product_tmpl_id integer,
                   uom_id integer,
                   lot_id character varying,
                   life_date date,
                   qty numeric,
                   stock integer
                 );


               -- variables ------------------------------------------------------------------------------------------------
	_sector_farmacia_id = (SELECT id FROM categoria WHERE lower(name) = 'farmacia' limit 1);
        -- _almacen = (SELECT almacen_id FROM stock_location WHERE id = _location_id);

	FOR _elementos_cur IN
	SELECT m.product_id as product_id, p.product_tmpl_id, pt.uom_id as uom_id,
		pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,
		sum(m.product_qty) AS cantidad
	FROM stock_move m
	INNER JOIN product_product p ON p.id = m.product_id
	INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
	INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque AND lower(te.name) like 'unitario'
	INNER JOIN stock_location l on l.id = m.location_id
	INNER JOIN stock_location sl on sl.id = m.location_dest_id
	INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
	WHERE m.date >= _fecha_desde::timestamp AND m.date <= _fecha_hasta::timestamp
		AND pick.code <> 'incoming'
	 	AND l.id = _location_id AND m.inventory_id IS NULL
	 	AND pt.categoria_id = _sector_farmacia_id
	GROUP BY m.product_id, p.product_tmpl_id, pt.uom_id, pt.principio_activo_id, pt.forma_farmaceutica_id,
		pt.concentracion_valor, pt.concentracion_unidad

                LOOP

                    _cantidad  := _elementos_cur.cantidad;

		    -- cesar
  		    _stock_maximo := 0;
		    _stock_actual := 0;


		   	--verificar el stock máximo y el stock actual --
			SELECT stock_maximo, COALESCE(stock_actual, 0 )
			INTO _stock_maximo, _stock_actual
			FROM sp_stock_critico_DU(_ubicacion_stock_almacen, _elementos_cur.principio_activo_id, _elementos_cur.forma_farmaceutica_id,
				_elementos_cur.concentracion_valor, _elementos_cur.concentracion_unidad);

			IF _stock_actual >= _stock_maximo THEN
			    _cantidad := 0;
			ELSE
			    _cantidad := _stock_maximo - _stock_actual;
			END IF;

                         IF _stock_actual is null THEN
				 _cantidad := _stock_maximo;
 	 		 END IF;

		    -- fin cesar

                    -- PRODUCTOS CON STOCK CON IGUAL GENERICO

                    FOR _genericos_cur IN
                    SELECT t.id, t.product_tmpl_id, t.uom_id, t.numero, t.vencimiento, t.cantidad
                    FROM (
                        SELECT p.id, p.product_tmpl_id, pt.uom_id,'SIN LOTE' AS numero, NOW() as vencimiento,
                            sum(sq.qty) as cantidad
                        FROM product_product p
                        INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                        INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque AND lower(te.name) like 'unitario'
                        INNER JOIN stock_quant sq on sq.product_id = p.id
                        LEFT JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
                        WHERE sq.location_id = _location_stock_id
                            AND pt.principio_activo_id = _elementos_cur.principio_activo_id
                            AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
                            AND pt.concentracion_valor = _elementos_cur.concentracion_valor
                            AND pt.concentracion_unidad = _elementos_cur.concentracion_unidad
                            AND sq.qty > 0
                            AND pt.active = true
                            AND l.product_id IS NULL
                            AND sq.reservation_id IS NULL
                            AND pt.categoria_id = _sector_farmacia_id
                        GROUP BY p.id, pt.uom_id, l.name, l.life_date

                        UNION ALL

                        SELECT p.id, p.product_tmpl_id, pt.uom_id, l.name as numero, l.life_date as vencimiento,
                            sum(sq.qty) as cantidad
                        FROM product_product p
                        INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                        INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque AND lower(te.name) like 'unitario'
                        INNER JOIN stock_quant sq on sq.product_id = p.id
                        INNER JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id

                        WHERE sq.location_id = _location_stock_id
                            AND pt.principio_activo_id = _elementos_cur.principio_activo_id
                            AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
                            AND pt.concentracion_valor = _elementos_cur.concentracion_valor
                            AND pt.concentracion_unidad = _elementos_cur.concentracion_unidad
                            AND sq.qty > 0
                            AND pt.active = true
                            AND sq.reservation_id IS NULL
                            AND pt.categoria_id = _sector_farmacia_id

                        GROUP BY p.id, pt.uom_id, l.name, l.life_date


                    ) AS t
                    ORDER BY t.vencimiento

                    LOOP

                        -- verificar si hay stock --------------------------------------------------------------------------------------------
                        IF _cantidad > _genericos_cur.cantidad THEN

                            -- no alcanza el stock, insertar este producto --
                            INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty, stock)
                            VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
                                _genericos_cur.vencimiento, _genericos_cur.cantidad, 1);

                            _cantidad := _cantidad - _genericos_cur.cantidad;

                        ELSE

                            -- alcanza el stock, insertar este producto y pasar al siguiente --
                            INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty, stock)
                            VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
                                _genericos_cur.vencimiento, _cantidad, 1);

                            _cantidad := 0;

                            exit;

                        END IF;

                    END LOOP;

                    IF _cantidad > 0 THEN

                        -- no alcanzo, insertar el producto original con el saldo --
                        INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty, stock)
                        VALUES(_elementos_cur.product_id, _elementos_cur.product_tmpl_id, _elementos_cur.uom_id, NULL,
                            NULL, _cantidad, 0);

                    END IF;

                END LOOP;

                return query select * from tmp_productos;

                -- Error Handle --------------------------------------------------------------------------------------------

                exception
                when others then
                GET STACKED DIAGNOSTICS _err_context = PG_EXCEPTION_CONTEXT;
                RAISE INFO 'Error Name:%',SQLERRM;
                RAISE INFO 'Error State:%', SQLSTATE;
                RAISE INFO 'Error Context:%', _err_context;
                --return query select * from tmp_productos where 1=2;
                return query select 0::integer as product_id,
				0::integer as product_tmpl_id,
				0::integer as uom_id,
				''::character varying as lot_id,
				now()::date as life_date,
				0::numeric as qty, 0 as stock;


            END;
            $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION public.sp_reponer_du(integer, integer, character varying, character varying)
  OWNER TO odoo;
