import pytest
import json
from domain.entities_and_dataclass.domain_dataclass import ODRoutingResult, AggregatedItinerary, AggregatedLeg, Itinerary, Leg, Point
from domain.entities_and_dataclass.domain_class import Stop, Route, Direction, Zone
from domain.domain_service.kpi_service.kpi_service import Cricuity_index_caculate, KPI_caculate, Tranfer_rate_caculate
from domain.domain_service.kpi_service.kpi_A_service import KPIASpatialCoverageService
from application.services.odresult_cal_kpi import CalKPI

def save_result_to_txt(od_id: str, results: dict, test_name: str):
    """Hàm phụ trợ lưu result ra file txt để debug/test."""
    output_filename = f"kpi_test_output_{test_name}_od_{od_id}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f"=== KPI Calculation Results for OD: {od_id} ===\n\n")
        
        for kpi_name, kpi_res_list in results.get("kpi_results", {}).items():
            f.write(f"--- {kpi_name} ---\n")
            for item in kpi_res_list:
                f.write(f"{item}\n")
            f.write("\n")
        
        f.write("=== Raw JSON ===\n")
        f.write(json.dumps(results, indent=4, ensure_ascii=False))

def test_cal_kpi_with_circuity_index():
    # Arrange
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    
    route1 = Route("R1", Direction.INBOUND, [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)], [s1, s2])
    
    iti = Itinerary([Leg("R1", "S1", "S2")])
    od_result = ODRoutingResult(
        od_id="OD_TEST_CIRCUITY", 
        aggregated_itineraries=[], 
        represent_itineraries=[iti]
    )
    
    calculators: list[KPI_caculate] = [Cricuity_index_caculate()]
    cal_kpi_service = CalKPI()
    
    # Act
    result = cal_kpi_service.cal_kpi(od_result, calculators, route_list=[route1])
    
    # Assert
    assert result["od_id"] == "OD_TEST_CIRCUITY"
    assert "Cricuity_index_caculate" in result["kpi_results"]
    assert len(result["kpi_results"]["Cricuity_index_caculate"]) == 1
    
    kpi_res = result["kpi_results"]["Cricuity_index_caculate"][0]["itinerary_0"]
    assert kpi_res["score"] >= 1.0
    
    # Lưu kết quả ra file Txt để Test
    save_result_to_txt(od_result.od_id, result, "circuity")

def test_cal_kpi_with_transfer_rate():
    # Arrange
    leg1 = AggregatedLeg("R1", {"S1"}, {"S2"})
    agg_iti = AggregatedItinerary([leg1])
    
    od_result = ODRoutingResult(
        od_id="OD_TEST_TRANSFER", 
        aggregated_itineraries=[agg_iti], 
        represent_itineraries=[]
    )
    
    calculators: list[KPI_caculate] = [Tranfer_rate_caculate()]
    cal_kpi_service = CalKPI()
    
    # Act
    result = cal_kpi_service.cal_kpi(od_result, calculators, route_list=[])
    
    # Assert
    assert "Tranfer_rate_caculate" in result["kpi_results"]
    assert len(result["kpi_results"]["Tranfer_rate_caculate"]) == 1
    
    kpi_res = result["kpi_results"]["Tranfer_rate_caculate"][0]["agg_itinerary_0"]
    assert kpi_res["score"] == "0"
    
    # Lưu kết quả ra file Txt để Test
    save_result_to_txt(od_result.od_id, result, "transfer")

def test_cal_multiple_kpis():
    # Arrange
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    route1 = Route("R1", Direction.INBOUND, [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.1, 0.1)], [s1, s2])
    
    leg1 = AggregatedLeg("R1", {"S1"}, {"S2"})
    agg_iti = AggregatedItinerary([leg1])
    iti = Itinerary([Leg("R1", "S1", "S2")])
    
    od_result = ODRoutingResult(
        od_id="OD_TEST_MULTIPLE", 
        aggregated_itineraries=[agg_iti], 
        represent_itineraries=[iti]
    )
    
    calculators: list[KPI_caculate] = [Tranfer_rate_caculate(), Cricuity_index_caculate()]
    cal_kpi_service = CalKPI()
    
    # Act
    result = cal_kpi_service.cal_kpi(od_result, calculators, route_list=[route1])
    
    # Assert
    assert "Tranfer_rate_caculate" in result["kpi_results"]
    assert "Cricuity_index_caculate" in result["kpi_results"]
    
    # Lưu kết quả ra file Txt để Test
    save_result_to_txt(od_result.od_id, result, "multiple")

def test_cal_kpi_with_spatial_coverage():
    # Arrange
    s1 = Stop("S1", 0.0, 0.0)
    s2 = Stop("S2", 0.1, 0.1)
    
    z1 = Zone("Z1", [Point(0.0, 0.0), Point(0.1, 0.0), Point(0.0, 0.1)], Point(0.05, 0.05))
    z2 = Zone("Z2", [Point(0.1, 0.1), Point(0.2, 0.1), Point(0.1, 0.2)], Point(0.15, 0.15))
    
    leg1 = AggregatedLeg("R1", {"S1"}, {"S2"})
    agg_iti = AggregatedItinerary([leg1])
    
    od_result = ODRoutingResult(
        od_id="OD_TEST_SPATIAL", 
        aggregated_itineraries=[agg_iti], 
        represent_itineraries=[]
    )
    
    # Mocking properties dually needed by odresult_cal_kpi.py currently if they were lost 
    od_result.origin_zone_id = "Z1"
    od_result.destination_zone_id = "Z2"
    
    # Truyền instance KPIASpatialCoverageService với dữ liệu zone/stop thực
    calculators: list[KPI_caculate] = [KPIASpatialCoverageService(zones=[z1, z2], stops=[s1, s2], stop_coverage_radius_m=500.0)]
    cal_kpi_service = CalKPI()
    
    # Act
    result = cal_kpi_service.cal_kpi(
        od_result, 
        calculators
    )
    
    # Assert
    assert "KPIASpatialCoverageService" in result["kpi_results"]
    assert len(result["kpi_results"]["KPIASpatialCoverageService"]) == 1
    
    kpi_res_dict = result["kpi_results"]["KPIASpatialCoverageService"][0]
    assert f"od_id_{od_result.od_id}" in kpi_res_dict
    
    # Lưu kết quả ra file Txt để Test
    save_result_to_txt(od_result.od_id, result, "spatial")

