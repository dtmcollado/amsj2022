
CREATE OR REPLACE FUNCTION public.sp_reponer_interno(
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
            _ubicacion_stock_almacen integer;
            _cantidad numeric;
            _stock_maximo numeric;
            _stock_actual numeric;
            _almacen integer;

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
        _almacen = (select almacen_id FROM stock_location WHERE id = _location_id);
	-- buscar la ubicacion de stock del almacen destino --
        _ubicacion_stock_almacen = (SELECT wh.lot_stock_id FROM stock_location l INNER JOIN stock_warehouse wh ON wh.id = l.almacen_id WHERE l.id = _location_id);
	--RAISE NOTICE '_ubicacion_stock_almacen --> %', _ubicacion_stock_almacen;


	-- buscar los productos que salieron de la ubicacion de stock --
	FOR _elementos_cur IN
	--SELECT m.product_id as product_id, p.product_tmpl_id, pt.uom_id as uom_id,
	--	pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,
	--	sum(m.product_qty) AS cantidad, pt.rmc
	--FROM stock_move m
	--INNER JOIN product_product p ON p.id = m.product_id
	--INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
	--INNER JOIN stock_location l on l.id = m.location_id
	--INNER JOIN stock_location sl on sl.id = m.location_dest_id
	--INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
	--WHERE m.date >= _fecha_desde::timestamp AND m.date <= _fecha_hasta::timestamp
	--	AND pick.code <> 'incoming'
	-- 	AND l.id = _ubicacion_stock_almacen
	-- 	AND pt.categoria_id = _sector_farmacia_id
	--GROUP BY m.product_id, p.product_tmpl_id, pt.uom_id, pt.principio_activo_id, pt.forma_farmaceutica_id,
	--	pt.concentracion_valor, pt.concentracion_unidad, pt.rmc
         SELECT
		 stock_move.product_id as product_id, p.product_tmpl_id, pt.uom_id as uom_id,
		pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,
		sum(stock_move.product_qty) AS cantidad, pt.rmc
                 FROM stock_move
                 INNER JOIN product_product p ON p.id = stock_move.product_id
                 INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
                 INNER JOIN stock_location sl ON sl.id = stock_move.location_dest_id
                    where
                          pt.categoria_id =  _sector_farmacia_id AND
                          stock_move.location_id = _location_id
                          AND sl.almacen_id = _almacen
                          AND (date >= _fecha_desde::timestamp and
                             date <= _fecha_hasta::timestamp)
                 GROUP BY stock_move.product_id, p.product_tmpl_id, pt.uom_id, pt.principio_activo_id, pt.forma_farmaceutica_id,
		pt.concentracion_valor, pt.concentracion_unidad, pt.rmc
                LOOP

                    _cantidad := _elementos_cur.cantidad;

		    IF _elementos_cur.rmc  THEN

			    -- SE REPONE POR MARCA COMERCIAL --
			    INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty, stock)
			    VALUES(_elementos_cur.product_id, _elementos_cur.product_tmpl_id, _elementos_cur.uom_id, NULL,
				NULL, _cantidad, 1);

		    ELSE

			    _stock_maximo := 0;
			    _stock_actual := 0;


				RAISE NOTICE '_cantidad --> %', _cantidad;
				RAISE NOTICE '_location_stock_id --> %', _ubicacion_stock_almacen;
				RAISE NOTICE 'elementos_cur.principio_activo_id --> %', _elementos_cur.principio_activo_id;
				RAISE NOTICE 'elementos_cur.forma_farmaceutica_id --> %', _elementos_cur.forma_farmaceutica_id;
				RAISE NOTICE 'elementos_cur.concentracion_valor --> %', _elementos_cur.concentracion_valor;
				RAISE NOTICE 'elementos_cur.concentracion_unidad --> %', _elementos_cur.concentracion_unidad;



			    -- verificar el stock máximo y el stock actual --
			    SELECT stock_maximo, stock_actual
			    INTO _stock_maximo, _stock_actual
			    FROM sp_stock_critico(_ubicacion_stock_almacen, _elementos_cur.principio_activo_id, _elementos_cur.forma_farmaceutica_id,
				_elementos_cur.concentracion_valor, _elementos_cur.concentracion_unidad);

				RAISE NOTICE '_stock_maximo --> %', _stock_maximo;
				RAISE NOTICE '_stock_actual --> %', _stock_actual;

			    IF _stock_maximo < _stock_actual THEN
				_cantidad := 0;
			    ELSE

				    IF (_stock_maximo - _stock_actual) < _cantidad THEN
					_cantidad := _stock_maximo - _stock_actual;
				    END IF;

			    END IF;
			    RAISE NOTICE '_cantidad2 --> %', _cantidad;
			    IF _cantidad > 0 THEN

				    -- HAY CANTIDAD A PEDIR

				    -- PRODUCTOS CON STOCK CON IGUAL GENERICO, FORMA FARMACEUTICA, CONCENTRACION

				    FOR _genericos_cur IN
				    SELECT t.id, t.product_tmpl_id, t.uom_id, t.numero, t.vencimiento, t.cantidad
				    FROM (
					SELECT p.id, p.product_tmpl_id, pt.uom_id, COALESCE(l.name ,'SIN LOTE') AS numero, COALESCE(l.life_date ,now()) as vencimiento,
					    sum(sq.qty) as cantidad
					FROM product_product p
					INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
					INNER JOIN stock_quant sq on sq.product_id = p.id
					LEFT JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
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
			    END IF;
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
ALTER FUNCTION public.sp_reponer_interno(integer, integer, character varying, character varying)
  OWNER TO odoo;
