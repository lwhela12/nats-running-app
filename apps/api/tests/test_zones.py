from app.domain.zones import derive_zones


def test_zones_shape_and_ordering():
    zones = derive_zones(10 * 60 * 60)  # very slow 10k
    assert "easy" in zones and "threshold" in zones
    e = zones["easy"]
    assert e["sec_per_km"][0] < e["sec_per_km"][1]

