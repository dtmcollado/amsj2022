SELECT
       co.product_tmpl_id, co.promedio as consumo_promedio ,
       pt.principio_activo_id,
       pt.forma_farmaceutica_id,
       pt.concentracion_valor,
       pt.concentracion_unidad, rp.id as proveedor ,pr.precio as costo
  FROM dtm_promedio_anual_consumo co
  JOIN product_template pt ON pt.id = co.product_tmpl_id
  LEFT JOIN dtm_precio_producto pr on pr.product_tmpl_id = co.product_tmpl_id
  LEFT JOIN product_supplierinfo psi ON psi.product_tmpl_id = pt.id
  LEFT JOIN res_partner rp ON rp.id = psi.name
  where co.categoria_id = 17