import jellyfish


def closest_string_match(string, s_list, th=0.85):
    """Calculate the Jaro similarity index between a given string and a every string in a given list of strings,
    a return the value with the highest similarity
    :param string: string to which calculate the closest match
    :param s_list: list of strings from which calculate the closest match
    :param th: threshold value. If no strings from s_list offer a similarity higher than th,
    the function will return None
    :return dic: dictionary containing the closest match and the Jaro similarity value
    """

    if string is None:
        dist = 0
    else:
        arr = [jellyfish.jaro_similarity(string.lower(), s.lower()) for s in s_list]
        dist = max(arr)
        idx = arr.index(dist)

    if dist > th:
        return {"value": s_list[idx], "jaro_similarity": dist}
    else:
        return {"value": None, "jaro_similarity": dist, "error_msg": "Could not find a value matching the "
                                                                     "threshold requirements"}


def rows_to_columns(arr):
    """Helper function for transforming an array filled of dictionaries (row wise format) into a dictionary where
    the values are arrays (columns wise format or dataframe format)
    :param arr: array containing information in a row wise format (e.g [{}, {}, {}]
    :return dic: dictionary with the information in dataframe format (e.g {"key1": [], "key2": []})"""
    cols = arr[0].keys()
    dic = {}
    for col in cols:
        dic[col] = []
        for elem in arr:
            dic[col].append(elem[col])
    return dic


def columns_to_rows(dic):
    """Helper function for transforming a dictionary where the values are
    arrays (columns wise format or dataframe format) into an array filled of dictionaries (row wise format)
    :param dic: dictionary with the information in dataframe format (e.g {"key1": [], "key2": []})
    :return arr: array containing information in a row wise format (e.g [{}, {}, {}]
    """
    cols = list(dic.keys())
    n = len(dic[cols[0]])
    arr = []
    for i in range(n):
        temp = {}
        for col in cols:
            temp[col] = dic[col][i]
        arr.append(temp)

    return arr


def generate_text(dic):
    """Generate a text out of a dictionary, placing each key value pair into a new line
    :param dic: dictionary
    :return: string generated out of dic"""

    text = ""
    for key in dic.keys():
        text += "{}: {} \n".format(str(key), str(dic[key]))

    return text
