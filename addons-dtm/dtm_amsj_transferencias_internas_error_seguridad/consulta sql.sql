SELECT sm.product_id , sum(sm.product_qty) as cantidad
FROM stock_move sm,stock_picking_type spt , stock_location loc
 where
    sm.picking_type_id = spt.id and
    spt.code = 'outgoing' and
    sm.location_id  = loc.id and
    sm.location_id  = 12
 group by sm.product_id;