drop table consumos_BI;
create table consumos_BI as
select   fecha as Fecha,
                          CodMSP,product_template_name,product_qty,
              ValorFIFOUnitario as FIFO_Unitario,
			  total_fifo as FIFO_Total,
	  		  ValorUltCompraUnit as PUC_Unitario,

              total_ultima_compra as PUC_Total ,
			  destino as UbicacionDestino,SUBSTRING(destino,6,30) as tipo , transaccion_id as id_transaccion
FROM

              sp_consumos_mov_report_BI('2020-07-25 00:00:00','2021-07-31 23:59:59','17',1,'','','') ;
