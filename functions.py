#calculates the power level of someone based on their level
def getPowerLevel(level):
    boundary_levels = {5:1,10:1,25:1,50:1,100:1}

    for boundary in boundary_levels:
        boundary_recorder = level // boundary
        boundary_levels[boundary] += boundary_recorder

    power_level_multipliers = 0

    for multiplier in boundary_levels:
        if power_level_multipliers == 0:
            power_level_multipliers = boundary_levels[multiplier]
        else:
            power_level_multipliers *= boundary_levels[multiplier]

    power_level = (level * 10) * power_level_multipliers
    return power_level

#fixing word such that each word is capitalized
def wordFilter(word):
        filter = word.split(" ")
        finish = ""
        for word in range(len(filter)):
            filter[word] = filter[word].lower()
            filter[word] = filter[word].title()
            if finish == "":
                finish = finish + filter[word]
            else:
                finish = finish + " " + filter[word] 
        return finish

#ranks bases based on their base power
def baseRanking(base_list):
    rankings = {}
    for times in range(10):
        for key in base_list:
            keyplace = key
            numberplace = base_list[key]

            for key2 in base_list:
                if base_list[key2] > numberplace:
                    numberplace = base_list[key2]
                    keyplace = key2
            rankings[keyplace] = numberplace
            break
        if len(base_list) != 0:
            base_list.pop(keyplace)
    return rankings
