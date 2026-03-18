WITH receita_por_cliente AS (
    SELECT
        v.id_cliente,
        c.nome_cliente,
        c.estado,
        SUM(v.receita_total) AS receita_total,
        COUNT(DISTINCT v.id_venda) AS total_compras,
        AVG(v.receita_total) AS ticket_medio,
        MIN(v.data_venda_date) AS primeira_compra,
        MAX(v.data_venda_date) AS ultima_compra
    FROM {{ ref('silver_vendas') }} v
    LEFT JOIN {{ ref('silver_clientes') }} c
        ON v.id_cliente = c.id_cliente
    GROUP BY v.id_cliente, c.nome_cliente, c.estado
)

SELECT
    rpc.id_cliente AS cliente_id,
    rpc.nome_cliente,
    rpc.estado,
    rpc.receita_total,
    rpc.total_compras,
    rpc.ticket_medio,
    rpc.primeira_compra,
    rpc.ultima_compra,
    rpc.ultima_compra - rpc.primeira_compra as diferenca_compra,
    CASE
        WHEN rpc.receita_total >= {{ var('segmentacao_vip_threshold', 10000) }} THEN 'VIP' 
        WHEN rpc.receita_total >= {{ var('segmentacao_top_tier_threshold', 5000) }} THEN 'TOP_TIER' 
        ELSE 'REGULAR'
    END AS segmento_cliente,
    ROW_NUMBER() OVER (ORDER BY rpc.receita_total DESC) AS ranking_receita
FROM receita_por_cliente rpc
ORDER BY rpc.receita_total DESC
