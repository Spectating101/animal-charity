.PHONY: test smoke landscape-smoke initiative-smoke control-smoke lifecycle-initiative-smoke preventive-smoke mbg-smoke public-good-smoke replay-smoke interop-smoke disaster-smoke disaster-evolution-smoke verify run seed docker-build

test:
	python -m unittest discover -s tests -v

smoke:
	@db=$$(mktemp /tmp/afrn-smoke-XXXXXX.db); rm -f "$$db"; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python scripts/seed_demo.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_AGENT_ONCE=1 python scripts/run_agent_loop.py >/dev/null; \
	AFRN_DB_PATH="$$db" AFRN_DEMO_MODE=1 python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); assert c.get('/health').json()['ok']; assert c.get('/v1/summary').status_code == 200"; \
	rm -f "$$db" "$$db-shm" "$$db-wal"

landscape-smoke:
	@python scripts/scan_landscape.py examples/taoyuan_public_baseline.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['cases']==[]; assert d['data_gaps']"
	@python scripts/scan_landscape.py examples/taoyuan_synthetic_incident.json | python -c "import json,sys; d=json.load(sys.stdin); c=d['cases'][0]; assert c['bottleneck']=='last_mile_logistics'; assert c['actuator']=='logistics.dispatch_request'"

initiative-smoke:
	@python scripts/plan_initiative.py examples/taoyuan_public_structural_baseline.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['structural_gap_established'] is False; assert d['recommended']['option_type']=='case_level_only'"
	@python scripts/plan_initiative.py examples/taoyuan_synthetic_structural_cluster.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['structural_gap_established'] is True; assert d['recommended']['option_type']=='weekly_pop_up_hub'; assert d['recommended']['site_id']=='synthetic-yangmei-host-a'"

control-smoke:
	@python scripts/assess_animal_welfare.py examples/zhongli_sanmin_policy_baseline.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['decisions']==[]; assert d['data_gaps']"
	@python scripts/assess_animal_welfare.py examples/zhongli_sanmin_synthetic_lifecycle.json | python -c "import json,sys; d=json.load(sys.stdin); kinds=[x['intervention_class'] for x in d['decisions']]; assert 'reunification' in kinds; assert 'owner_retention' in kinds; assert kinds.count('source_control')==3; assert 'foster_to_adoption' in kinds; assert 'specialist_referral' in kinds; assert 'rescue_stabilize' in kinds; assert any(x['intervention_class']=='source_control' for x in d['structural_signals'])"

lifecycle-initiative-smoke:
	@python scripts/plan_lifecycle_initiatives.py examples/zhongli_sanmin_synthetic_source_control_history.json | python -c "import json,sys; d=json.load(sys.stdin); assert len(d)==1; p=d[0]; assert p['structural_gap_established'] is True; assert p['intervention_class']=='source_control'; assert p['recommended']['mode']=='periodic_pop_up'; assert p['recommended']['site_id']=='synthetic-sanmin-community-host'"

preventive-smoke:
	@python scripts/assess_preventive_welfare.py examples/zhongli_sanmin_synthetic_preventive_system.json | python -c "import json,sys; d=json.load(sys.stdin); o=[x for x in d['prevention_opportunities'] if x['intervention_class']=='source_control']; assert len(o)==3; assert all(x['structural_candidate'] for x in o); assert all(x['causal_status']=='hypothesis' for x in o); assert d['access_gaps']; assert 'rights' in d['transfer_boundary']"

mbg-smoke:
	@python scripts/assess_mbg_case.py examples/mbg_banten_public_context.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['findings']==[]; assert d['data_gaps']; assert 'insufficient' in d['safe_conclusion'].lower()"
	@python scripts/assess_mbg_case.py examples/mbg_synthetic_integrity_case.json | python -c "import json,sys; d=json.load(sys.stdin); kinds=[x['problem_class'] for x in d['findings']]; assert d['integrity_assessment']['overall_status']=='audit_referral_recommended'; assert kinds[0]=='integrity_uncertainty'; assert 'capacity_gap' not in kinds; assert 'corruption' in d['safe_conclusion'].lower()"
	@python scripts/assess_mbg_case.py examples/mbg_synthetic_capacity_case.json | python -c "import json,sys; d=json.load(sys.stdin); kinds=[x['problem_class'] for x in d['findings']]; assert d['integrity_assessment']['overall_status']=='normal'; assert 'capacity_gap' in kinds; assert 'integrity_uncertainty' not in kinds"

public-good-smoke:
	@python scripts/assess_public_good_case.py examples/public_good_animal_owner_retention.json | python -c "import json,sys; d=json.load(sys.stdin); f=d['normalized_findings'][0]; assert d['domain']=='animal_welfare'; assert f['stage']=='prevent'; assert f['domain_detail']['intervention_class']=='owner_retention'; assert 'veterinary_gap' in f['recommended_action']"
	@python scripts/assess_public_good_case.py examples/public_good_mbg_integrity.json | python -c "import json,sys; d=json.load(sys.stdin); stages=[x['stage'] for x in d['normalized_findings']]; assert d['domain']=='mbg_public_nutrition'; assert stages[0]=='integrity'; assert 'capacity' not in stages; assert 'audit' in d['normalized_findings'][0]['recommended_action'].lower()"
	@python scripts/assess_public_good_case.py examples/public_good_mbg_capacity.json | python -c "import json,sys; d=json.load(sys.stdin); stages=[x['stage'] for x in d['normalized_findings']]; assert 'capacity' in stages; assert 'integrity' not in stages; c=next(x for x in d['normalized_findings'] if x['stage']=='capacity'); assert c['structural_candidate']"

replay-smoke:
	@python scripts/replay_public_good_case.py examples/replay_animal_owner_retention.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['reference_hidden'] is True; assert d['assessment']['normalized_findings'][0]['stage']=='prevent'; assert 'historical_action' not in d"
	@python scripts/replay_public_good_case.py examples/replay_mbg_integrity.json --score | python -c "import json,sys; d=json.load(sys.stdin); assert d['predicted_primary_stage']=='integrity'; assert d['primary_stage_match'] is True"
	@python scripts/replay_public_good_case.py examples/replay_disaster_kubu_raya_2026_08_07.json --score | python -c "import json,sys; d=json.load(sys.stdin); assert d['predicted_primary_stage']=='evidence'; assert d['primary_stage_match'] is True"
	@python scripts/replay_public_good_case.py examples/replay_disaster_ntt_2026_08_15_0800.json --score | python -c "import json,sys; d=json.load(sys.stdin); assert d['predicted_primary_stage']=='safety'; assert d['primary_stage_match'] is True"

interop-smoke:
	@python scripts/build_control_plane_packet.py examples/interop_kalimantan_synthetic.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['hazards'][0]['hazard_type']=='wildfire'; assert len(d['deployable_resources'])==1; assert len(d['resource_candidates_requiring_verification'])==1; assert d['command_contexts']"
	@python scripts/build_control_plane_packet.py examples/interop_ntt_synthetic.json | python -c "import json,sys; d=json.load(sys.stdin); kinds=[x['resource_type'] for x in d['deployable_resources']]; assert 'urban_search_and_rescue_team' in kinds; assert 'potable_water_tanker' not in kinds; assert 'stale-road-report' in d['stale_record_ids']"

disaster-smoke:
	@python scripts/assess_disaster.py examples/disaster_ntt_synthetic.json | python -c "import json,sys; d=json.load(sys.stdin); assert d['command_context_present']; assert any(x['stage']=='safety' for x in d['findings']); assert len([x for x in d['proposed_reservations'] if x['resource_record_id']=='sar-team-a'])==1; assert any(x['problem_class']=='potable_water_capacity_gap' for x in d['findings']); assert any(x['stage']=='access' for x in d['findings'])"
	@python scripts/assess_disaster.py examples/disaster_kalimantan_synthetic.json | python -c "import json,sys; d=json.load(sys.stdin); assert any(x['problem_class']=='fire_suppression_resource_route' for x in d['findings']); assert any(x['problem_class']=='reported_resource_requires_verification' for x in d['findings']); assert any(x['problem_class']=='medical_existing_service_route' for x in d['findings'])"

disaster-evolution-smoke:
	@python scripts/compare_disaster_periods.py examples/disaster_ntt_synthetic.json examples/disaster_ntt_synthetic_t1.json | python -c "import json,sys; d=json.load(sys.stdin); assert 'trapped-a' in d['explicitly_resolved_need_ids']; assert 'water-a' in d['missing_followup_need_ids']; assert 'sar-team-a' in d['lost_deployable_resource_ids']; assert 'medevac-air-a' in d['newly_deployable_resource_ids']; assert d['recommendation_stage_changes']['isolated-medical-a']['from']=='access'; assert d['recommendation_stage_changes']['isolated-medical-a']['to']=='route'"

verify: test smoke landscape-smoke initiative-smoke control-smoke lifecycle-initiative-smoke preventive-smoke mbg-smoke public-good-smoke replay-smoke interop-smoke disaster-smoke disaster-evolution-smoke
	python -m compileall -q app scripts tests

run:
	fastapi dev app/main.py

seed:
	python scripts/seed_demo.py

docker-build:
	docker build -t animal-feed-relief-network:local .
