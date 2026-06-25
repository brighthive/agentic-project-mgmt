-- =============================================================================
-- ASPIRATIONAL — domain-agnostic warehouse template (REFERENCE ONLY, not seeded)
-- =============================================================================
-- One fixed warehouse structure; swap the synthetic DATA per domain, keep the
-- SCHEMA identical. NOT what local_bootstrap loads today (that's the Longaeva
-- finance schema under ../postgres/). Captured so the design isn't lost — see
-- BH-764 and the dogfood README. Dialect here is illustrative (Redshift/Snowflake
-- SUPER + JSON_PARSE/JSON_EXTRACT_PATH_TEXT); a Postgres port would use jsonb +
-- ->> accessors.
--
-- The warehouse structure (all 5 layers) is IDENTICAL across domains.
-- Only these change per domain:
--   1. dim_workspace.domain_type tag
--   2. dim_subject  — who the entity is
--   3. dim_program  — what they participate in / consume / receive
--   4. dim_provider — who delivers the program
--   5. fact_enrollment.status vocabulary
--   6. fact_outcome.outcome_type vocabulary
--   7. Any domain_view_* aliases (optional, for readability)
--
-- All agent / pipeline / governance / lineage tables are UNCHANGED. They don't
-- care what domain the data is in.
-- =============================================================================

-- ── DOMAIN A: AUTOMOTIVE / VEHICLE FLEET ──────────────────────────────────────
-- subject=vehicle  program=service_plan  provider=dealership
-- enrollment=service/recall  outcome=repair_completed|recall_resolved|inspection_passed
INSERT INTO bh_platform.dim_workspace VALUES
    ('ws-auto-001', 'org-001', 'FleetOps Analytics', 'fleetops', 'automotive', 'prod', '555000000001', 'active', NOW());
INSERT INTO bh_domain.dim_subject VALUES
    ('subj-a001', 'ws-auto-001', 'VIN-1HGBH41JXMN109186', 'fleet_q1_2026', 'high_mileage',
     JSON_PARSE('{"make":"Honda","model":"Accord","year":2019,"odometer_miles":87420}'), 'fleet_mgmt_system', NOW()),
    ('subj-a002', 'ws-auto-001', 'VIN-3VWFE21C04M000001', 'fleet_q1_2026', 'recall_pending',
     JSON_PARSE('{"make":"Volkswagen","model":"Golf","year":2020,"odometer_miles":43100}'), 'fleet_mgmt_system', NOW());
INSERT INTO bh_domain.dim_provider VALUES
    ('prov-a001', 'ws-auto-001', 'Sunset Honda Service Center', 'authorized_dealer', 'Los Angeles, CA', '441110', TRUE, NOW());
INSERT INTO bh_domain.dim_program VALUES
    ('prog-a001', 'ws-auto-001', '30K Mile Maintenance Package', 'scheduled_maintenance', 'prov-a001', 1, 349.99, 500, TRUE,
     JSON_PARSE('{"services":["oil","brakes","tires"],"warranty_months":12}'), NOW());
INSERT INTO bh_domain.fact_enrollment VALUES
    ('enr-a001', 'ws-auto-001', 'subj-a001', 'prog-a001', 20260401, 20260402, 'completed', NULL, NOW());
INSERT INTO bh_domain.fact_outcome VALUES
    ('out-a001', 'ws-auto-001', 'subj-a001', 'prog-a001', 20260402, 'repair_completed', 1, 'boolean', TRUE, 'enr-a001', NULL, NOW());

-- ── DOMAIN B: FOOD & GROCERY SUPPLY CHAIN ─────────────────────────────────────
-- subject=sku  program=supply_contract  provider=supplier
-- outcome=fill_rate|on_time_delivery|waste_pct|promo_lift_pct
INSERT INTO bh_platform.dim_workspace VALUES
    ('ws-food-001', 'org-002', 'Grocery Supply Analytics', 'grocery_supply', 'food_supply', 'prod', '555000000002', 'active', NOW());
INSERT INTO bh_domain.dim_subject VALUES
    ('subj-f001', 'ws-food-001', 'SKU-0041196000049', 'perishable_q2_2026', 'high_velocity',
     JSON_PARSE('{"name":"Organic Whole Milk 1gal","category":"dairy","shelf_life_days":14}'), 'erp_system', NOW());
INSERT INTO bh_domain.dim_provider VALUES
    ('prov-f001', 'ws-food-001', 'Organic Valley Cooperative', 'dairy_supplier', 'La Farge, WI', '311511', TRUE, NOW());
INSERT INTO bh_domain.dim_program VALUES
    ('prog-f001', 'ws-food-001', 'Dairy Weekly Replenishment Contract', 'replenishment_contract', 'prov-f001', 7, NULL, NULL, TRUE,
     JSON_PARSE('{"min_fill_rate":0.95,"lead_time_days":2}'), NOW());
INSERT INTO bh_domain.fact_enrollment VALUES
    ('enr-f001', 'ws-food-001', 'subj-f001', 'prog-f001', 20260601, NULL, 'enrolled', NULL, NOW());
INSERT INTO bh_domain.fact_outcome VALUES
    ('out-f001', 'ws-food-001', 'subj-f001', 'prog-f001', 20260607, 'fill_rate', 0.97, 'pct', TRUE, 'enr-f001', NULL, NOW());

-- ── DOMAIN C: TECHNOLOGY / SAAS SUBSCRIPTIONS ─────────────────────────────────
-- subject=customer_account  program=subscription_plan  provider=csm_team
-- outcome=nrr|churn_risk_score|product_adoption_score|expansion_arr
INSERT INTO bh_platform.dim_workspace VALUES
    ('ws-tech-001', 'org-001', 'SaaS Revenue Intelligence', 'saas_revenue', 'tech_services', 'prod', '555000000003', 'active', NOW());
INSERT INTO bh_domain.dim_subject VALUES
    ('subj-t001', 'ws-tech-001', 'ACCT-ACME-00419', 'ent_cohort_2024', 'expansion_candidate',
     JSON_PARSE('{"company":"Acme Corp","industry":"manufacturing","arr_usd":48000}'), 'crm_salesforce', NOW());
INSERT INTO bh_domain.dim_provider VALUES
    ('prov-t001', 'ws-tech-001', 'Enterprise CSM Pod', 'internal_csm', 'AMER', NULL, TRUE, NOW());
INSERT INTO bh_domain.dim_program VALUES
    ('prog-t001', 'ws-tech-001', 'Enterprise Plan — Annual', 'subscription', 'prov-t001', 365, 48000.00, NULL, TRUE,
     JSON_PARSE('{"sla_uptime":0.9999,"support":"24x7"}'), NOW());
INSERT INTO bh_domain.fact_enrollment VALUES
    ('enr-t001', 'ws-tech-001', 'subj-t001', 'prog-t001', 20260101, 20261231, 'enrolled', NULL, NOW());
INSERT INTO bh_domain.fact_outcome VALUES
    ('out-t001', 'ws-tech-001', 'subj-t001', 'prog-t001', 20260601, 'nrr_pct', 118, 'pct', TRUE, 'enr-t001', NULL, NOW());

-- ── DOMAIN D: FASHION & CLOTHING RETAIL ───────────────────────────────────────
-- subject=product_variant  program=collection/markdown  provider=brand
-- outcome=sell_through_pct|return_rate|inventory_days|margin_pct
INSERT INTO bh_platform.dim_workspace VALUES
    ('ws-fashion-001', 'org-002', 'Retail Merchandising Hub', 'merch_hub', 'fashion_retail', 'prod', '555000000004', 'active', NOW());
INSERT INTO bh_domain.dim_subject VALUES
    ('subj-cl001', 'ws-fashion-001', 'SKU-WD-BLAZER-BLK-M', 'SS26_womens', 'core',
     JSON_PARSE('{"item":"Wool Blend Blazer","color":"black","size":"M","retail_usd":195.00}'), 'merchandising_system', NOW());
INSERT INTO bh_domain.dim_provider VALUES
    ('prov-cl001', 'ws-fashion-001', 'Milano Tailoring Group', 'manufacturer', 'Milan, Italy', '315210', TRUE, NOW());
INSERT INTO bh_domain.dim_program VALUES
    ('prog-cl001', 'ws-fashion-001', 'Spring/Summer 2026 Core Collection', 'seasonal_collection', 'prov-cl001', 180, NULL, NULL, TRUE,
     JSON_PARSE('{"season":"SS26","target_sell_through":0.75}'), NOW());
INSERT INTO bh_domain.fact_enrollment VALUES
    ('enr-cl001', 'ws-fashion-001', 'subj-cl001', 'prog-cl001', 20260301, 20260831, 'enrolled', NULL, NOW());
INSERT INTO bh_domain.fact_outcome VALUES
    ('out-cl001', 'ws-fashion-001', 'subj-cl001', 'prog-cl001', 20260601, 'sell_through_pct', 0.58, 'pct', TRUE, 'enr-cl001', NULL, NOW());

-- ── CROSS-DOMAIN: agent cost per session by domain ────────────────────────────
-- Works because dim_workspace.domain_type tags each workspace; agent tables are
-- domain-blind.
--   SELECT w.domain_type, COUNT(DISTINCT s.session_id) AS sessions,
--          SUM(s.total_cost_usd) AS total_agent_cost_usd
--   FROM bh_agent.fact_agent_session s
--   JOIN bh_platform.dim_workspace w ON s.workspace_id = w.workspace_id
--   GROUP BY w.domain_type ORDER BY total_agent_cost_usd DESC;

-- ── VOCABULARY REFERENCE ──────────────────────────────────────────────────────
-- dim_subject.segment:
--   automotive:    new | high_mileage | recall_pending | fleet
--   food_supply:   perishable | high_velocity | seasonal | slow_mover
--   tech_services: healthy | churn_risk | expansion_candidate | new
--   fashion_retail:core | trend | overstock | clearance
--   workforce:     high_barrier | returning | job_ready | placed
-- fact_outcome.outcome_type:
--   automotive:    repair_completed | recall_resolved | inspection_passed | safety_risk_score
--   food_supply:   fill_rate | on_time_delivery | waste_pct | transit_hours | cold_chain_breach
--   tech_services: product_adoption_score | nrr_pct | churn_risk_score | expansion_arr_usd
--   fashion_retail:sell_through_pct | return_rate_pct | inventory_days | gross_margin_pct
--   workforce:     job_placement | credential_earned | wage_at_placement | days_to_employment
-- =============================================================================
