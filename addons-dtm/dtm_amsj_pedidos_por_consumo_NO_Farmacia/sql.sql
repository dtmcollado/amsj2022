-- Function: sp_reponer(integer, integer, character varying, character varying)

-- DROP FUNCTION sp_reponer(integer, integer, character varying, character varying);

CREATE OR REPLACE FUNCTION sp_reponer(
    IN _location_id integer,
    IN _location_stock_id integer,
    IN _fecha_desde character varying,
    IN _fecha_hasta character varying)
  RETURNS TABLE(product_id integer, product_tmpl_id integer, uom_id integer, lot_id character varying, life_date date, qty integer) AS
$BODY$
DECLARE

--crear una tabla temporal para ir insertando los productos que voy a elegir

_elementos_cur record;
_genericos_cur record;
_sector_farmacia_id integer;
_cantidad integer;

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
	   qty integer
	 );


	-- variables ------------------------------------------------------------------------------------------------
	_sector_farmacia_id = (SELECT id FROM categoria WHERE lower(name) = 'farmacia' limit 1);


	FOR _elementos_cur IN
	SELECT m.product_id as product_id, p.product_tmpl_id, pt.uom_id as uom_id,
		pt.principio_activo_id, pt.forma_farmaceutica_id, pt.concentracion_valor, pt.concentracion_unidad,
		sum(m.product_qty) AS cantidad
	FROM stock_move m
	INNER JOIN product_product p ON p.id = m.product_id
	INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
	INNER JOIN stock_location l on l.id = m.location_id
	INNER JOIN stock_picking_type pick on pick.id = m.picking_type_id
	WHERE m.date >= _fecha_desde::date AND m.date <= _fecha_hasta::date
		AND l.principal_del_expendio = true
		AND pick.code <> 'incoming'
	 	AND l.id=_location_id
	 	AND pt.categoria_id = _sector_farmacia_id
	GROUP BY m.product_id, p.product_tmpl_id, pt.uom_id, pt.principio_activo_id, pt.forma_farmaceutica_id,
		pt.concentracion_valor, pt.concentracion_unidad

	LOOP

		_cantidad  := _elementos_cur.cantidad;
		-- PRODUCTOS CON STOCK CON IGUAL GENERICO

		FOR _genericos_cur IN
		SELECT t.id, t.product_tmpl_id, t.uom_id, t.numero, t.vencimiento, t.cantidad
		FROM (
			SELECT p.id, p.product_tmpl_id, pt.uom_id,'SIN LOTE' AS numero, NOW() as vencimiento,
				sum(sq.qty) as cantidad
			FROM product_product p
			INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
			INNER JOIN stock_quant sq on sq.product_id = p.id
			LEFT JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id
			WHERE sq.location_id = _location_stock_id
				AND pt.principio_activo_id = _elementos_cur.principio_activo_id
				AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
				AND pt.concentracion_valor = _elementos_cur.concentracion_valor
				AND pt.concentracion_valor = _elementos_cur.concentracion_valor
				AND sq.qty > 0
				AND l.product_id IS NULL
				AND sq.reservation_id IS NULL
				AND pt.categoria_id = _sector_farmacia_id
			GROUP BY p.id, pt.uom_id, l.name, l.life_date


			UNION ALL

			SELECT p.id, p.product_tmpl_id, pt.uom_id, l.name as numero, l.life_date as vencimiento,
				sum(sq.qty) as cantidad
			FROM product_product p
			INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
			INNER JOIN stock_quant sq on sq.product_id = p.id
			INNER JOIN stock_production_lot l on l.product_id = sq.product_id AND sq.lot_id = l.id

			WHERE sq.location_id = _location_stock_id
				AND pt.principio_activo_id = _elementos_cur.principio_activo_id
				AND pt.forma_farmaceutica_id = _elementos_cur.forma_farmaceutica_id
				AND pt.concentracion_valor = _elementos_cur.concentracion_valor
				AND pt.concentracion_valor = _elementos_cur.concentracion_valor
				AND sq.qty > 0
				AND sq.reservation_id IS NULL
				AND pt.categoria_id = _sector_farmacia_id

			GROUP BY p.id, pt.uom_id, l.name, l.life_date


		) AS t
		ORDER BY t.vencimiento

		LOOP

			-- verificar si hay stock --------------------------------------------------------------------------------------------
			IF _cantidad > _genericos_cur.cantidad THEN

				-- no alcanza el stock, insertar este producto --
				INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
				VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
					_genericos_cur.vencimiento, genericos_cur.cantidad);

				_cantidad := _cantidad - genericos_cur.cantidad;

			ELSE

				-- alcanza el stock, insertar este producto y pasar al siguiente --
				INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
				VALUES(_genericos_cur.id, _genericos_cur.product_tmpl_id, _genericos_cur.uom_id, _genericos_cur.numero,
					_genericos_cur.vencimiento, _cantidad);

				_cantidad := 0;

				exit;

			END IF;


		END LOOP;

		IF _cantidad > 0 THEN

			-- no alcanzo, insertar el producto original con el saldo --
			INSERT INTO tmp_productos (product_id, product_tmpl_id, uom_id, lot_id, life_date, qty)
			VALUES(_elementos_cur.product_id, _elementos_cur.product_tmpl_id, _elementos_cur.uom_id, NULL,
				NULL, _cantidad);

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
	return query select * from tmp_productos where 1=2;


END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION sp_reponer(integer, integer, character varying, character varying)
  OWNER TO odoo;
