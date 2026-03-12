-- ============================================
-- Post-Import Verification Queries
-- Run after: python3 db/import_aul.py
-- Usage:     psql risk_assessment_db < db/verify_aul_import.sql
-- ============================================

-- 1. Row counts
\echo '--- Row Counts ---'
SELECT 'materials' AS table_name, COUNT(*) AS row_count FROM materials
UNION ALL
SELECT 'shops', COUNT(*) FROM shops
UNION ALL
SELECT 'material_authorizations', COUNT(*) FROM material_authorizations;
-- Expected: materials = 11,025 | shops = 354 | material_authorizations ≈ 26,759

-- 2. Sample search by shop code (Krystal's primary use case)
\echo ''
\echo '--- Sample: Shop Code 054C-Z01 ---'
SELECT ma.msn, m.noun, ma.process_name, ma.max_on_hand
FROM material_authorizations ma
JOIN materials m ON ma.msn = m.msn
WHERE ma.shop_code = '054C-Z01';

-- 3. Sample search by MSN
\echo ''
\echo '--- Sample: MSN 6810PHM00513939 ---'
SELECT ma.shop_code, s.org_symbol, ma.process_name
FROM material_authorizations ma
JOIN shops s ON ma.shop_code = s.shop_code
WHERE ma.msn = '6810PHM00513939';

-- 4. Detect any remaining exact-duplicate authorizations
--    Groups by ALL fact-table columns to match the import's duplicate definition.
--    Expected result: 0 rows.
\echo ''
\echo '--- Exact Duplicate Check (expect 0 rows) ---'
SELECT msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand, COUNT(*)
FROM material_authorizations
GROUP BY msn, shop_code, process_name, local_process_name, dist_pct, max_on_hand
HAVING COUNT(*) > 1;

-- 5. Inspect the resolved noun conflict
\echo ''
\echo '--- Noun Conflict Resolution Check ---'
SELECT msn, noun FROM materials WHERE msn = '8030013234503';
-- Expected: noun = 'SEALANT, SILICONE, BLUE, GASKETS' (majority-wins heuristic)
