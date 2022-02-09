-- DROP FUNCTION public.sp_consumo_rango_fechas(character varying, character varying, integer, integer, integer);

CREATE OR REPLACE FUNCTION public.sp_consumo_rango_fechas(
    IN _fecha_desde character varying,
    IN _fecha_hasta character varying,
    IN _location_id integer,
    IN _tipo_compra integer,
    IN _sector integer)
  RETURNS TABLE("Fecha" character varying, "Código" character varying, "Producto" character varying, "Cantidad" numeric, "Origen" character varying, "Destino" character varying) AS
$BODY$
DECLARE

BEGIN

RETURN query

SELECT p."Fecha", p."Código", p."Producto", p."Cantidad", p."Origen", p."Destino"
FROM (

    SELECT p.fecha::character varying AS "Fecha",
    p.default_code::character varying AS "Código",
        p.name::character varying AS "Producto",
    p."Cantidad"::numeric,
    origen.complete_name::character varying AS "Origen",
    destino.complete_name::character varying AS "Destino"

    FROM (

            SELECT TO_CHAR(m.date, 'YYYY-MM') as fecha, p.default_code, pt.name, m.location_id, m.location_dest_id, sum(m.product_qty) AS "Cantidad"
            FROM stock_move m
            INNER JOIN product_product p ON p.id = m.product_id
            INNER JOIN product_template pt ON pt.id = p.product_tmpl_id AND pt.categoria_id = _sector
            WHERE m.date >= _fecha_desde::date AND m.date <= _fecha_hasta::date
        AND m.location_id = _location_id
                --AND (coalesce(sl.scrap_location,false) = true OR sl.usage = 'customer')
            GROUP BY TO_CHAR(m.date, 'YYYY-MM'), p.default_code, pt.name, m.location_id, m.location_dest_id

    ) AS p
    INNER JOIN stock_location as origen ON origen.id = p.location_id
    INNER JOIN stock_location as destino ON destino.id = p.location_dest_id



) AS p
ORDER BY p."Producto";

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 10000;
ALTER FUNCTION public.sp_consumo_rango_fechas(character varying, character varying, integer, integer, integer)
  OWNER TO odoo;
