from idunn.utils.pj_address_normalization import normalized_pj_address


def test_pj_address_normalisation():
    assert normalized_pj_address("5 r Thorigny") == "5 rue Thorigny"
    assert normalized_pj_address("171 bd Montparnasse") == "171 boulevard Montparnasse"
    assert normalized_pj_address("171 BD MONTPARNASSE") == "171 boulevard Montparnasse"
    assert normalized_pj_address("5 pl Charles Béraudier") == "5 place Charles Béraudier"
    assert normalized_pj_address("5 av G De Gaule") == "5 avenue G De Gaule"
    assert normalized_pj_address("5 r avé") == "5 rue Avé"
    assert normalized_pj_address("Avenue A. R. Guibert") == "avenue A. R. Guibert"
    assert normalized_pj_address("10 rue D.R.F") == "10 rue D.R.F"
    assert normalized_pj_address("10 r de l'Ave Maria") == "10 rue De L'Ave Maria"
    assert normalized_pj_address("10 R DE L'AVE MARIA") == "10 rue De L'Ave Maria"
    assert normalized_pj_address("10 rue ste Catherine") == "10 rue Sainte Catherine"
    assert normalized_pj_address("186 crs ZAC des Charmettes") == "186 cours Zac Des Charmettes"
    assert normalized_pj_address("10 BOULEVARD r garros") == "10 boulevard R Garros"
    assert normalized_pj_address("60 RUE ST PIERRE") == "60 rue Saint Pierre"
    assert normalized_pj_address("6 quai Mar Joffre") == "6 quai Maréchal Joffre"
    assert normalized_pj_address("13 qua Mar Joffre") == "13 quartier Maréchal Joffre"
    assert normalized_pj_address("6 Allée du Cor de Chasse") == "6 allée Du Cor De Chasse"
    assert normalized_pj_address("13 r du Cor de Chasse") == "13 rue Du Cor De Chasse"
    assert normalized_pj_address("ZI 10 chem Petit") == "Zi 10 chemin Petit"
