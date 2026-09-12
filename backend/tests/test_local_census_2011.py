from app.services.demographics.census_2011 import administrative_options, subdistrict_snapshot


def test_imported_census_provides_fast_hierarchy_and_demographics():
    districts = administrative_options("district", "state:uttar-pradesh", "Uttar Pradesh", None)
    assert districts is not None
    assert districts.status == "AVAILABLE"
    assert any(option.name == "Saharanpur" for option in districts.options)

    subdistricts = administrative_options("block", "census-district:09:001", "Uttar Pradesh", "Saharanpur")
    assert subdistricts is not None
    assert subdistricts.status == "AVAILABLE"
    first = subdistricts.options[0]
    snapshot = subdistrict_snapshot("Uttar Pradesh", "Saharanpur", first.name)
    assert snapshot is not None
    assert snapshot.total_population > 0
