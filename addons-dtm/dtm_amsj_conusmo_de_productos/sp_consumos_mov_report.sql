-- Function: public.sp_consumos_mov_report(character varying, character varying, character varying, integer, character varying, text, character varying)

DROP FUNCTION public.sp_consumos_mov_report(character varying, character varying, character varying, integer, character varying, text, character varying);

CREATE OR REPLACE FUNCTION public.sp_consumos_mov_report(
    IN _fecha_desde character varying,
    IN _fecha_hasta character varying,
    IN _sector_ids character varying,
    IN _es_de_consumo integer,
    IN _categoria_ids character varying,
    IN _origen_ids text,
    IN _destino_ids character varying)
  RETURNS TABLE(sector character varying, categoria_interna character varying, product_template_id integer, product_template_name character varying, via_de_administracion character varying, sema_ucor boolean, codigo_geosalud character varying, principio_activo character varying, familia character varying, grupo character varying, subgrupo character varying, forma_farmaceutica character varying, costo double precision, origen character varying, destino character varying, centro_costos integer, cost double precision, product_qty double precision, sector_id integer, categoria_interna_id integer, grupo_id integer, subgrupo_id integer, forma_farmaceutica_id integer, principio_activo_id integer, familia_id integer, fecha timestamp without time zone, ftm boolean, destino_id integer, origen_id integer, codmsp character varying, total_fifo double precision, total_ultima_compra double precision, almacen_origen character varying, almacen_destino character varying, id integer, rubro_centro_entrada character varying, rubro_centro_salida character varying, valorfifounitario double precision, valorultcompraunit double precision, usuario character varying, rubroentrada character varying, rubrosalida character varying, proveedor character varying, es_de_consumo integer, rubro character varying, codigo character varying, rubro_consumo character varying, codigo_consumo character varying, inventory_id integer) AS
$BODY$
DECLARE

BEGIN

    -- INICIO TABLAS TEMPORALES ----------------------------------------------------------------------------------------------------

    -- MOVIMIENTOS SALIDAS
    DROP TABLE IF EXISTS temp_stock_move_salidas; 
    CREATE TEMP TABLE temp_stock_move_salidas as
    SELECT * FROM stock_move m
    WHERE m.date >= _fecha_desde::timestamp without time zone AND m.date <= _fecha_hasta::timestamp without time zone
        AND (m.location_id <> 557) 
        AND (m.location_id = ANY(string_to_array(_origen_ids,',','0')::int[]) OR _origen_ids = '')
        AND (m.location_dest_id = ANY(string_to_array(_destino_ids,',','0')::int[]) OR _destino_ids = '')
        AND m.state = 'done';

    CREATE INDEX ON temp_stock_move_salidas (id);

    -- QUANTS SALIDAS EL PRIMERO
    DROP TABLE IF EXISTS temp_stock_quant_move_rel_salidas; 
    CREATE TEMP TABLE temp_stock_quant_move_rel_salidas as
    SELECT sqmr.move_id, min(sqmr.quant_id) AS quant_id 
    FROM stock_quant_move_rel sqmr
    INNER JOIN temp_stock_move_salidas m ON m.id = sqmr.move_id
    GROUP BY sqmr.move_id;
   
   CREATE INDEX ON temp_stock_quant_move_rel_salidas (move_id);

    -- FACTURAS
    DROP TABLE IF EXISTS temp_facturas; 
    CREATE TEMP TABLE temp_facturas as
    SELECT product_tmpl_id, max(price_unit) as precio_ultima_compra , max(name):: character varying as proveedor
    FROM (
    
            SELECT p.product_tmpl_id, ail.price_unit, pro.name
            FROM account_invoice ai
            INNER JOIN account_invoice_line ail ON ai.id = ail.invoice_id
            INNER JOIN res_partner pro ON pro.id = ai.partner_id
            INNER JOIN product_product p ON p.id = ail.product_id
            INNER JOIN (

                SELECT ail.product_id, max(date_invoice) AS date_invoice
                FROM account_invoice ai
                INNER JOIN account_invoice_line ail ON ai.id = ail.invoice_id 
                WHERE ai.state in ('draft','open','paid')
                AND date_invoice <= _fecha_hasta::timestamp without time zone
                AND ai."type" = 'in_invoice'
                GROUP BY ail.product_id
                
            ) AS d ON d.product_id = ail.product_id AND d.date_invoice = ai.date_invoice
            WHERE ai.state in ('draft','open','paid')
                AND ai."type" = 'in_invoice' 
            
    ) AS t
    GROUP BY product_tmpl_id; 

    CREATE INDEX ON temp_facturas (product_tmpl_id);
    
    -- MOVIMIENTOS DEVOLUCIONES
    DROP TABLE IF EXISTS temp_stock_move_devoluciones; 
    CREATE TEMP TABLE temp_stock_move_devoluciones as
    SELECT * FROM stock_move m
    WHERE m.date >= _fecha_desde::timestamp without time zone AND m.date <= _fecha_hasta::timestamp without time zone
        AND (m.location_dest_id <> 557) 
        AND (m.location_dest_id = ANY(string_to_array(_origen_ids,',','0')::int[]) OR _origen_ids = '')
        AND (m.location_id = ANY(string_to_array(_destino_ids,',','0')::int[]) OR _destino_ids = '')
        AND m.state = 'done';
    
    CREATE INDEX ON temp_stock_move_devoluciones (id);

    -- QUANTS DEVOLUCIONES EL PRIMERO
    DROP TABLE IF EXISTS temp_stock_quant_move_rel_devoluciones; 
    CREATE TEMP TABLE temp_stock_quant_move_rel_devoluciones as
    SELECT sqmr.move_id, min(sqmr.quant_id) AS quant_id 
    FROM stock_quant_move_rel sqmr
    INNER JOIN temp_stock_move_devoluciones m ON m.id = sqmr.move_id
    GROUP BY sqmr.move_id;
    
    CREATE INDEX ON temp_stock_quant_move_rel_devoluciones (move_id);
    
RETURN query

 
  SELECT c.name AS sector,
    t.name AS categoria_interna,
    pt.id AS product_template_id,
    pt.name AS product_template_name,
    via_admin.name AS via_de_administracion,
    pt.sema_ucor,
    pt.codigo_geosalud,
    prin_activo.name AS principio_activo,
    fa.name AS familia,
    gr.name AS grupo,
    sub.name AS subgrupo,
    forma.name AS forma_farmaceutica,
    
    (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(ip.precio_ultima_compra,0) > 0 then ip.precio_ultima_compra
    else coalesce(pr.precio,0) end) AS costo,
    
    replace(l.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS origen,
    replace(l2.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS destino,
    0 AS centro_costos,
    
    (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(ip.precio_ultima_compra,0) > 0 then ip.precio_ultima_compra
    else coalesce(pr.precio,0) end) AS cost,
    
    m.product_qty::double precision,
    c.id AS sector_id,
    pt.categ_id AS categoria_interna_id,
    gr.id AS grupo_id,
    sub.id AS subgrupo_id,
    forma.id AS forma_farmaceutica_id,
    prin_activo.id AS principio_activo_id,
    fa.id AS familia_id,
    m.date AS fecha,
    pt.ftm,
    m.location_dest_id AS destino_id,
    m.location_id AS origen_id,
    p.default_code AS codmsp,
    
    m.product_qty * (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(ip.precio_ultima_compra,0) > 0 then ip.precio_ultima_compra
    else coalesce(pr.precio,0) end)::numeric(18,2)::double precision AS total_fifo,

    (case when coalesce(ip.precio_ultima_compra,0) > 0 then  m.product_qty * coalesce(ip.precio_ultima_compra,0)::numeric(18,2)::double precision
     else  m.product_qty * coalesce(pr.precio,0) end)::numeric(18,2)::double precision AS total_ultima_compra,
    
    
    almacen_entrada.name AS almacen_origen,
    almacen_salida.name AS almacen_destino,
    l.id,
    centro_entrada.name AS rubro_centro_entrada,
    centro_salida.name AS rubro_centro_salida,
    (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    else coalesce(pr.precio,0) end)::numeric(18,2)::double precision AS ValorFIFOUnitario,

    (case when coalesce(ip.precio_ultima_compra,0) > 0 then coalesce(ip.precio_ultima_compra,0)::numeric(18,2)::double precision
     else coalesce(pr.precio,0) end)::numeric(18,2)::double precision AS ValorUltCompraUnit,
    
    
    usuario.name as usuario,
    centro_entrada.rubro AS rubro_entrada,
    centro_salida.rubro AS rubro_salida,
    ip.proveedor,
    CASE
         WHEN (coalesce(l2.scrap_location,false) = true OR l2.usage = 'customer') and (lower(te.name) <> 'unitario') THEN 1
         WHEN (l2.id IN(7)) and (lower(te.name) <> 'unitario') THEN 1
         WHEN (lower(te.name) = 'unitario') THEN 0
         ELSE 0
    END as de_consumo, /* 1 = verdadero, 0 = falso */
    ru.rubro , ru.codigo , ro.rubro as rubro_consumo , ro.codigo as codigo_consumo, m.inventory_id as inventory_id
   FROM temp_stock_move_salidas m
     INNER JOIN temp_stock_quant_move_rel_salidas ON temp_stock_quant_move_rel_salidas.move_id = m.id
     INNER JOIN stock_quant quant ON temp_stock_quant_move_rel_salidas.quant_id = quant.id
     INNER JOIN stock_location l ON l.id = m.location_id
     INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
     INNER JOIN product_product p ON p.id = m.product_id
     INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
     INNER JOIN dtm_precio_producto pr ON pr.product_tmpl_id = p.product_tmpl_id
     LEFT JOIN tipo_empaque te on te.id = pt.tipo_de_empaque  
     INNER JOIN product_category t ON t.id = pt.categ_id
     INNER JOIN res_users u ON u.id = m.write_uid
     INNER JOIN res_partner usuario ON usuario.id = u.partner_id
     LEFT JOIN temp_facturas AS ip ON ip.product_tmpl_id = p.product_tmpl_id
     LEFT JOIN dtm_rubro_de_consumo ru ON ru.producto_id = p.id
     LEFT JOIN dtm_rubro ro ON ro.producto_id = p.id
     LEFT JOIN categoria c ON c.id = pt.categoria_id
     LEFT JOIN grupo gr ON pt.grupo_id = gr.id
     LEFT JOIN via_de_administracion via_admin ON pt.via_de_administracion = via_admin.id
     LEFT JOIN principio_activo prin_activo ON pt.principio_activo_id = prin_activo.id
     LEFT JOIN familia fa ON pt.familia_id = fa.id
     LEFT JOIN subgrupo sub ON pt.subgrupo_id = sub.id
     LEFT JOIN forma_farmaceutica forma ON pt.forma_farmaceutica_id = forma.id
     LEFT JOIN stock_warehouse almacen_entrada ON almacen_entrada.id = l.almacen_id
     LEFT JOIN stock_warehouse almacen_salida ON almacen_salida.id = l2.almacen_id
     LEFT JOIN centro_costo centro_entrada ON centro_entrada.id = almacen_entrada.centro_costos
     LEFT JOIN centro_costo centro_salida ON centro_salida.id = almacen_salida.centro_costos
  WHERE  l.usage::text = 'internal'::text 
    AND ( ((CASE
         WHEN (coalesce(l2.scrap_location,false) = true OR l2.usage = 'customer') and (lower(te.name) <> 'unitario') THEN 1
         WHEN (l2.id IN(7)) and (lower(te.name) <> 'unitario') THEN 1
         WHEN (lower(te.name) = 'unitario') THEN 0
         ELSE 0
        END = 1) OR _es_de_consumo = 0) OR ( m.location_id IN (520) ) )
    AND (pt.categoria_id = ANY(string_to_array(_sector_ids,',','0')::int[]) OR _sector_ids = '')
    AND (pt.categ_id = ANY(string_to_array(_categoria_ids,',','0')::int[]) OR _categoria_ids = '')
   
 union all 

 
 SELECT c.name AS sector,
    t.name AS categoria_interna,
    pt.id AS product_template_id,
    pt.name AS product_template_name,
    via_admin.name AS via_de_administracion,
    pt.sema_ucor,
    pt.codigo_geosalud,
    prin_activo.name AS principio_activo,
    fa.name AS familia,
    gr.name AS grupo,
    sub.name AS subgrupo,
    forma.name AS forma_farmaceutica,
    (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(pr.precio,0) > 0 and coalesce(m.price_unit,0) = 0 then pr.precio
    else coalesce(ip.precio_ultima_compra,0) end) * -1 AS costo,
    
    replace(l2.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS origen,
    replace(l.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS destino,
    0 AS centro_costos,
    (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(pr.precio,0) > 0 then pr.precio
    else coalesce(ip.precio_ultima_compra,0) end) * -1 as cost,
    (m.product_qty * -1)::double precision,
    c.id AS sector_id,
    pt.categ_id AS categoria_interna_id,
    gr.id AS grupo_id,
    sub.id AS subgrupo_id,
    forma.id AS forma_farmaceutica_id,
    prin_activo.id AS principio_activo_id,
    fa.id AS familia_id,
    m.date AS fecha,
    pt.ftm,
    m.location_dest_id AS origen_id,
    m.location_id   AS destino_id,
    p.default_code AS codmsp,
    
    m.product_qty * -1 * (case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(pr.precio,0) > 0 and coalesce(m.price_unit,0) = 0 then pr.precio
    else coalesce(ip.precio_ultima_compra ,0) end)::numeric(18,2)::double precision AS total_fifo,

    (case when coalesce(ip.precio_ultima_compra,0) > 0 then  m.product_qty * coalesce(ip.precio_ultima_compra * -1 ,0)::numeric(18,2)::double precision
     else  m.product_qty * coalesce(pr.precio * -1 ,0) end)::numeric(18,2)::double precision AS total_ultima_compra,

    
    almacen_salida.name AS almacen_origen,
    almacen_entrada.name AS almacen_destino,
    l.id,
    centro_entrada.name AS rubro_centro_entrada,
    centro_salida.name AS rubro_centro_salida,
    ((case when coalesce(quant.cost,0) > 0 and coalesce(m.price_unit,0) > 0 then 
        case when quant.cost > m.price_unit * 1.2 then m.price_unit
        else quant.cost end 
    when coalesce(m.price_unit,0) > 0 then m.price_unit
    when coalesce(pr.precio,0) > 0 and coalesce(m.price_unit,0) = 0 then pr.precio
    else coalesce(ip.precio_ultima_compra,0) end) * -1)::numeric(18,2)::double precision AS ValorFIFOUnitario,

    (case when coalesce(ip.precio_ultima_compra,0) > 0 then coalesce(ip.precio_ultima_compra * -1,0)::numeric(18,2)::double precision
     else coalesce(pr.precio * -1 ,0) end)::numeric(18,2)::double precision AS ValorUltCompraUnit,

    usuario.name as usuario,
    centro_entrada.rubro AS rubro_entrada,
    centro_salida.rubro AS rubro_salida,  
    ip.proveedor,
    CASE
         WHEN (coalesce(l.scrap_location,false) = true OR l.usage = 'customer') and (lower(te.name) <> 'unitario') THEN 1
         WHEN (l2.id IN(7)) and (lower(te.name) <> 'unitario') THEN 1
         WHEN (lower(te.name) = 'unitario') THEN 0
         ELSE 0
    END as de_consumo, 
    ru.rubro , ru.codigo , ro.rubro as rubro_consumo , ro.codigo as codigo_consumo, m.inventory_id as inventory_id
    FROM temp_stock_move_devoluciones m
     INNER JOIN temp_stock_quant_move_rel_devoluciones ON temp_stock_quant_move_rel_devoluciones.move_id = m.id
     INNER JOIN stock_quant quant ON temp_stock_quant_move_rel_devoluciones.quant_id = quant.id
     INNER JOIN stock_location l ON l.id = m.location_id
     INNER JOIN stock_location l2 ON l2.id = m.location_dest_id
     INNER JOIN product_product p ON p.id = m.product_id
     INNER JOIN product_template pt ON pt.id = p.product_tmpl_id
     INNER JOIN dtm_precio_producto pr ON pr.product_tmpl_id = p.product_tmpl_id
     INNER JOIN tipo_empaque te on te.id = pt.tipo_de_empaque  
     INNER JOIN product_category t ON t.id = pt.categ_id
     INNER JOIN res_users u ON u.id = m.write_uid
     INNER JOIN res_partner usuario ON usuario.id = u.partner_id
     LEFT JOIN temp_facturas AS ip ON ip.product_tmpl_id = p.product_tmpl_id
     LEFT JOIN dtm_rubro_de_consumo ru ON ru.producto_id = p.id
     LEFT JOIN dtm_rubro ro ON ro.producto_id = p.id
     LEFT JOIN categoria c ON c.id = pt.categoria_id
     LEFT JOIN grupo gr ON pt.grupo_id = gr.id
     LEFT JOIN via_de_administracion via_admin ON pt.via_de_administracion = via_admin.id
     LEFT JOIN principio_activo prin_activo ON pt.principio_activo_id = prin_activo.id
     LEFT JOIN familia fa ON pt.familia_id = fa.id
     LEFT JOIN subgrupo sub ON pt.subgrupo_id = sub.id
     LEFT JOIN forma_farmaceutica forma ON pt.forma_farmaceutica_id = forma.id
     LEFT JOIN stock_warehouse almacen_entrada ON almacen_entrada.id = l.almacen_id
     LEFT JOIN stock_warehouse almacen_salida ON almacen_salida.id = l2.almacen_id
     LEFT JOIN centro_costo centro_entrada ON centro_entrada.id = almacen_salida.centro_costos
     LEFT JOIN centro_costo centro_salida ON centro_salida.id =  almacen_entrada.centro_costos

  WHERE (l2.usage::text = 'internal'::text AND l.id <> 8)
    AND ( ((CASE
         WHEN (coalesce(l.scrap_location,false) = true OR l.usage = 'customer') and (lower(te.name) <> 'unitario') THEN 1
         WHEN (l.id IN(7)) and (lower(te.name) <> 'unitario') THEN 1
         WHEN (lower(te.name) = 'unitario') THEN 0
         ELSE 0
        END = 1) OR _es_de_consumo = 0) OR ( m.location_dest_id IN (520) ) )
    AND (pt.categoria_id = ANY(string_to_array(_sector_ids,',','0')::int[]) OR _sector_ids = '')
    AND (pt.categ_id = ANY(string_to_array(_categoria_ids,',','0')::int[]) OR _categoria_ids = '')
    
  ORDER BY fecha;



END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 10000;
ALTER FUNCTION public.sp_consumos_mov_report(character varying, character varying, character varying, integer, character varying, text, character varying)
  OWNER TO odoo;
