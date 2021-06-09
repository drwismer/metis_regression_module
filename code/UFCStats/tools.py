def strip_remove_blanks(list_a):
    list_a = [x.strip() for x in list_a]
    list_a = [x for x in list_a if x]
    return list_a


def time_to_sec(time):
    try:
        min_sec = time.split(':')
        sec = int(min_sec[1])
        min_in_sec = int(min_sec[0])*60
    except (IndexError, TypeError) as e:
        return e
    return sec + min_in_sec

def judge_round_scores(round_scores, f1_list, f2_list, j, correct_position):
    if correct_position:
        f1_list.append(round_scores[j+1])
        f2_list.append(round_scores[j+2])
    else:
        f2_list.append(round_scores[j+1])
        f1_list.append(round_scores[j+2])