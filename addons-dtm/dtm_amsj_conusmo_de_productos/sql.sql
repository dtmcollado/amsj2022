-- Function: sp_fifo(character varying, character varying)

-- DROP FUNCTION sp_consulta_fifo(character varying, character varying);

CREATE OR REPLACE FUNCTION sp_consulta_fifo(
    IN _fecha_desde character varying,
    IN _fecha_hasta character varying)
  RETURNS TABLE(product_id integer, promedio_AFIFADO double precision) AS
$BODY$
DECLARE
BEGIN

	RETURN query
	SELECT t.product_id, case when sum(t.cantidad) > 0 then sum(t.valor) / sum(t.cantidad) else 0 end as valor
	FROM
		(
			SELECT 'inicial' as tipo, sum(quantity) as cantidad, sum(price_unit_on_quant * quantity) as valor , product_id
			FROM stock_history
			where date < _fecha_desde::date
			group by product_id

			union all

			SELECT 'final' as tipo, sum(quantity) * -1 as cantidad, sum(price_unit_on_quant * quantity) * -1 as valor , product_id
			FROM stock_history
			where date <= _fecha_hasta::date
			group by product_id

			union all

			select 'compras' as tipo, sum(quantity) as cantidad, sum(price_unit_on_quant * quantity) as valor , stock_history.product_id
			FROM stock_history
			INNER JOIN stock_move s ON s.id = stock_history.move_id
			INNER JOIN stock_location l ON l.usage = 'supplier' and s.location_id = l.id
			where (stock_history.date >= _fecha_desde::date and stock_history.date <= _fecha_hasta::date)
			group by stock_history.product_id

		) as t
	GROUP BY t.product_id;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 10000;
ALTER FUNCTION sp_consulta_fifo(character varying, character varying)
  OWNER TO "odoo";