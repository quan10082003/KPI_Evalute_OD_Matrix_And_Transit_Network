from infrastructure.repositories.cottbus_xml_repository import CottbusXmlRepository
from domain.entities_and_dataclass.domain_class import ODPair, Zone
from domain.entities_and_dataclass.domain_dataclass import Point


def test_load_network_and_demand_returns_only_connected_od_pairs(monkeypatch):
    repository = CottbusXmlRepository(
        schedule_path="dummy_schedule.xml",
        plans_path="dummy_plans.xml",
        max_plans=10,
    )

    zone_1 = Zone("Z1", [], Point(0.0, 0.0))
    zone_2 = Zone("Z2", [], Point(1.0, 1.0))
    zone_3 = Zone("Z3", [], Point(2.0, 2.0))
    zone_4 = Zone("Z4", [], Point(3.0, 3.0))

    od_connected = ODPair("OD_CONNECTED", zone_1, zone_2, 5)
    od_disconnected = ODPair("OD_DISCONNECTED", zone_3, zone_4, 7)

    monkeypatch.setattr(repository, "_parse_stops", lambda: [])
    monkeypatch.setattr(repository, "_parse_routes", lambda stops: [])
    monkeypatch.setattr(
        repository,
        "_parse_zones_and_od_pairs",
        lambda: ([zone_1, zone_2, zone_3, zone_4], [od_connected, od_disconnected]),
    )
    monkeypatch.setattr(
        repository,
        "_is_od_connected",
        lambda od_pair, routes: od_pair.id == "OD_CONNECTED",
    )

    stops, routes, zones, od_pairs = repository.load_network_and_demand()

    assert stops == []
    assert routes == []
    assert [od.id for od in od_pairs] == ["OD_CONNECTED"]
    assert {zone.id for zone in zones} == {"Z1", "Z2"}
