from idunn.geocoder.nlu_client import NLU_Helper


def test_classifier_handle_response():
    cat_for = NLU_Helper.nlu_classifier_handle_response
    assert cat_for({"intention": []}) is None
    assert cat_for({"intention": [(0.10, "restaurant")]}) is None
    assert cat_for({"intention": [(0.99, "restaurant")]}).value == "restaurant"
    assert cat_for({"intention": [(0.99, "restaurant"), (0.90, "pharmacy")]}) is None
    assert cat_for({"intention": [(0.99, "restaurant"), (0.20, "unk")]}) is None
    assert cat_for({"intention": [(0.99, "restaurant"), (0.01, "unk")]}).value == "restaurant"
