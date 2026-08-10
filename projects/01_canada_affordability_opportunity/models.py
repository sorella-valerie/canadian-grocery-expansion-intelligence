FEDERAL = [(58523, .14), (117045, .205), (181440, .26), (258482, .29), (float("inf"), .33)]
PROVINCIAL = {
    "BC": [(49279, .0506), (98560, .077), (113158, .105), (137407, .1229), (186306, .147), (259829, .168), (float("inf"), .205)],
    "AB": [(61200, .08), (154259, .10), (185111, .12), (246813, .13), (370220, .14), (float("inf"), .15)],
    "SK": [(54532, .105), (155805, .125), (float("inf"), .145)],
    "MB": [(47000, .108), (100000, .1275), (float("inf"), .174)],
    "ON": [(53891, .0505), (107785, .0915), (150000, .1116), (220000, .1216), (float("inf"), .1316)],
    "QC": [(53255, .14), (106495, .19), (129590, .24), (float("inf"), .2575)],
    "NB": [(52333, .094), (104666, .14), (193861, .16), (float("inf"), .195)],
    "NS": [(30995, .0879), (61991, .1495), (97417, .1667), (157124, .175), (float("inf"), .21)],
}


def progressive_tax(income, brackets):
    tax, floor = 0.0, 0.0
    for ceiling, rate in brackets:
        taxable = max(0.0, min(income, ceiling) - floor)
        tax += taxable * rate
        floor = ceiling
        if income <= ceiling:
            break
    return tax


def estimate_take_home(gross, province_code):
    gross = max(float(gross), 0.0)
    tax = progressive_tax(gross, FEDERAL) + progressive_tax(gross, PROVINCIAL[province_code])
    cpp = min(max(gross - 3500, 0) * .0595, 4230.45) + min(max(gross - 74600, 0) * .04, 416)
    ei = min(gross * .0163, 1123.07)
    return max(gross - tax - cpp - ei, 0)


def affordability_label(rent_share, remaining):
    if remaining < 0 or rent_share >= .5:
        return "High risk"
    if rent_share >= .35 or remaining < 750:
        return "Stretched"
    return "Affordable"


