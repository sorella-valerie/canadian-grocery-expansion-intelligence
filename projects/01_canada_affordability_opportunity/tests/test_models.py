from models import affordability_label, estimate_take_home


def test_take_home_is_bounded():
    assert 0 < estimate_take_home(55000, "ON") < 55000


def test_labels():
    assert affordability_label(.25, 1200) == "Affordable"
    assert affordability_label(.40, 500) == "Stretched"
    assert affordability_label(.55, -10) == "High risk"

