from application.use_cases.evaluate_network_use_case import EvaluateNetworkUseCase
from domain.entities_and_dataclass.domain_class import ODPair, Zone
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult, Point


class DummyRepository:
    def __init__(self, stops, routes, zones, od_pairs):
        self._stops = stops
        self._routes = routes
        self._zones = zones
        self._od_pairs = od_pairs

    def load_network_and_demand(self):
        return self._stops, self._routes, self._zones, self._od_pairs


def test_execute_integrates_produce_and_kpi_services(monkeypatch):
    zone_1 = Zone("Z1", [], Point(0.0, 0.0))
    zone_2 = Zone("Z2", [], Point(1.0, 1.0))

    od_valid = ODPair("OD_VALID", zone_1, zone_2, 10)
    od_same_zone = ODPair("OD_SKIP", zone_1, zone_1, 3)

    use_case = EvaluateNetworkUseCase(
        repository=DummyRepository(stops=[], routes=[], zones=[zone_1, zone_2], od_pairs=[od_valid, od_same_zone])
    )

    mocked_result = ODRoutingResult(
        od_id="OD_VALID",
        aggregated_itineraries=[],
        represent_itineraries=[],
    )

    captured = {}

    def fake_produce(route_list=None, stop_list=None, zone_list=None, od_pair_list=None):
        captured["od_pair_ids"] = [od.id for od in od_pair_list]
        return [mocked_result]

    def fake_cal_kpi(od_routing_results, kpi_calculators, route_list=None, **kwargs):
        captured["calculator_types"] = [type(cal).__name__ for cal in kpi_calculators]
        captured["origin_zone_id"] = od_routing_results.origin_zone_id
        captured["destination_zone_id"] = od_routing_results.destination_zone_id
        captured["travel_demand"] = od_routing_results.travel_demand
        return {"od_id": od_routing_results.od_id, "kpi_results": {"ok": True}}

    exported = {}

    def fake_export_json(kpi_report, output_json_path, meta):
        exported["kpi_report"] = kpi_report
        exported["output_json_path"] = output_json_path
        exported["meta"] = meta

    monkeypatch.setattr(use_case.od_result_producer, "produce_od_result", fake_produce)
    monkeypatch.setattr(use_case.kpi_calculator, "cal_kpi", fake_cal_kpi)
    monkeypatch.setattr(use_case, "_export_json", fake_export_json)

    output_path = "output.json"
    use_case.execute(output_path)

    assert captured["od_pair_ids"] == ["OD_VALID"]
    assert captured["calculator_types"] == [
        "Tranfer_rate_caculate",
        "Cricuity_index_caculate",
        "KPIASpatialCoverageService",
    ]
    assert captured["origin_zone_id"] == "Z1"
    assert captured["destination_zone_id"] == "Z2"
    assert captured["travel_demand"] == 10

    assert exported["kpi_report"]["od_kpi_results"][0]["od_id"] == "OD_VALID"
    assert exported["meta"]["total_od_pairs_evaluated"] == 1
    assert exported["output_json_path"] == output_path


def test_use_case_no_longer_exposes_old_private_steps():
    assert not hasattr(EvaluateNetworkUseCase, "_preprocess")
    assert not hasattr(EvaluateNetworkUseCase, "_calculate_kpis")
