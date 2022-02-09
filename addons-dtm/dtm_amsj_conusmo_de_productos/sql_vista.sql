CREATE OR REPLACE VIEW public.consumos_fefo_report AS
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
    m.product_qty,
    replace(l.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS origen,
    replace(l2.complete_name::text, 'Physical Locations / '::text, ''::text)::character varying AS destino,
    m.centro_costos,
    quant.cost,
    quant.qty AS quantity,
    c.id AS sector_id,
    pt.categ_id AS categoria_interna_id,
    gr.id AS grupo_id,
    sub.id AS subgrupo_id,
    forma.id AS forma_farmaceutica_id,
    prin_activo.id AS principio_activo_id,
    fa.id AS familia_id,
    m.date AS fecha,
    pt.ftm,
    l2.id AS destino_id,
    l.id AS origen_id,
    p.default_code AS codmsp,
    quant.qty * m.price_unit::numeric(18,2)::double precision AS total_fifo,
    quant.qty * ip.value_float::numeric(18,2)::double precision AS total_ultima_compra
   FROM stock_move m
     JOIN stock_location l ON l.id = m.location_id
     JOIN stock_location l2 ON l2.id = m.location_dest_id
     JOIN product_product p ON p.id = m.product_id
     JOIN product_template pt ON pt.id = p.product_tmpl_id
     JOIN product_category t ON t.id = pt.categ_id
     JOIN ir_property ip ON ip.res_id::text = ('product.template,'::text || p.product_tmpl_id)
     JOIN ir_model_fields imf ON imf.id = ip.fields_id AND imf.name::text = 'standard_price'::text
     LEFT JOIN categoria c ON c.id = pt.categoria_id
     LEFT JOIN stock_quant_move_rel ON stock_quant_move_rel.move_id = m.id
     LEFT JOIN stock_quant quant ON stock_quant_move_rel.quant_id = quant.id
     LEFT JOIN grupo gr ON pt.grupo_id = gr.id
     LEFT JOIN via_de_administracion via_admin ON pt.via_de_administracion = via_admin.id
     LEFT JOIN principio_activo prin_activo ON pt.principio_activo_id = prin_activo.id
     LEFT JOIN familia fa ON pt.familia_id = fa.id
     LEFT JOIN subgrupo sub ON pt.subgrupo_id = sub.id
     LEFT JOIN forma_farmaceutica forma ON pt.forma_farmaceutica_id = forma.id
  WHERE (l2.scrap_location = true OR l2.usage::text = 'customer'::text) AND quant.qty > 0::double precision;
