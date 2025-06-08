Hay un  tema que preocupa.

Debería hacer un cierre anual de las tabla registro_financiero_apartamento, a excepción de los apartamentos morosos, que tienen mas de 24 meses de deuda por ejemplo.

Me parece mucho computo para estar revisando el estado de cuenta de cada apartamento, y para ello ver todo el historial de pagos, y ver si hay morosidad o no.

Como cubrir este tema?, como lo ves?, que opinas?.

Respuesta:
4. Vista optimizada para consultas de morosidad:
   - Crear una vista que muestre solo los apartamentos con morosidad, filtrando por aquellos que tienen más de 24 meses de deuda.
   - Esta vista puede ser utilizada para generar reportes y tomar decisiones sobre el cierre anual.

```sql   
CREATE OR REPLACE VIEW vista_estado_apartamentos AS
SELECT 
    a.id,
    a.identificador,
    p.nombre_completo,
    sa.saldo_total,
    sa.meses_mora,
    sa.fecha_ultimo_pago,
    CASE 
        WHEN sa.meses_mora >= 12 THEN 'MOROSIDAD_CRITICA'
        WHEN sa.meses_mora >= 4 THEN 'MOROSIDAD_MEDIA'
        WHEN sa.meses_mora >= 1 THEN 'MOROSIDAD_LEVE'
        ELSE 'AL_DIA'
    END as estado_morosidad
FROM apartamento a
LEFT JOIN propietario p ON a.propietario_id = p.id
LEFT JOIN saldo_apartamento sa ON a.id = sa.apartamento_id 
WHERE sa.año = EXTRACT(YEAR FROM CURRENT_DATE);
```

Frente a tu respuesta me surgen otras preguntas:

1. ¿Script para generación de Cargos?
    - Considero que tal vez hace su función, dado que no lo he revisado a fondo, pero tal vez se necesite complementar porque en lo que se tiene actualmente y en virtud de que hay una tabla de interés anual, no veo y me gustaría que los cargos de interés se hagan de forma automática, además de que no se tenga que estar reprocesando frecuentemente, es decir, si ya se calculan los intereses de mora de un mes.