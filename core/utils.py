

def data_masking(username):
    # Make data masking, except for first 4 characters.
    OPENED_CHARACTERS_NUMBER = 4

    username = str(username)
    hidden_id_result = username[:OPENED_CHARACTERS_NUMBER] + "*" * (len(username)-OPENED_CHARACTERS_NUMBER)
    return hidden_id_result