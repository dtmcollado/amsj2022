CREATE OR REPLACE VIEW public.diferencia_precio_ordenes_facturas AS
SELECT ai.id as id_factura, po.id as id_orden,
                    ai.partner_id, rp.name as proveedor,
                    ai.supplier_invoice_number,

                    ai.date_invoice,
                    po.name as purchase_order,
                    po.date_order,
                    ail.product_id,
                    pt.name,
                    pp.default_code as referencia_interna, ail.price_unit as precio_factura,
                     pol.price_unit as precio_orden
                FROM account_invoice ai
                    inner join account_invoice_line ail
                        on ail.invoice_id = ai.id and not lower(ail.name) like '%redondeo%'
                    inner join stock_picking sp
                        on sp.name = ai.origin
                    inner join purchase_order po on po.name = sp.origin
                    inner join purchase_order_line pol on pol.order_id = po.id and pol.product_id = ail.product_id
                    inner join product_product pp on pp.id = pol.product_id
                    inner join product_template pt on pt.id = pp.product_tmpl_id
                    inner join res_partner rp on rp.id = ai.partner_id
                where not ai.origin is null and pol.price_unit != ail.price_unit;

ALTER TABLE public.diferencia_precio_ordenes_facturas
  OWNER TO odoo;
