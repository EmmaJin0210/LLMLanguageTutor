from openai import OpenAI
from utils import *
import datetime

def create_test_set(language, grammar_dict):
    testset = {}
    client = OpenAI()
    sys_prompt = "You are a helpful sentence generator."
    sys_prompt += "Given a grammar point in {language} and its meaning, you should generate a full sentence in {language} "
    sys_prompt += "that utilizes the grammar point given, or its direct conjugation."
    sys_prompt += "Make sure that the sentence you generate actually uses the grammar point in {language}, not just some other grammar point with the same meaning."

    for gp, to_unpack in grammar_dict.items():
        meaning = to_unpack["meaning"]
        query = gp + ", " + meaning
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": "にする, to decide on"},
                {"role": "assistant", "content": "彼は日本語を勉強することにしました"},
                {"role": "user", "content": "たり～たり, do such things as A and B"},
                {"role": "assistant", "content": "休みの日は映画を見たり、友達と買い物をしたりします"},
                {"role": "user", "content": "い-adjectives, i-adjectives"},
                {"role": "assistant", "content": "その料理は美味しいです"},
                {"role": "user", "content": query}
            ]
        )
        model_output = completion.choices[0].message.content
        testset[gp] = model_output
    return testset

grammar_dict = load_grammar_file_to_dict("japanese", ["n5"])
test_set = create_test_set("japanese", grammar_dict)
current_time = datetime.datetime.now()
timestamp = current_time.strftime("%Y-%m-%d-%H-%M-%S")
filename = f"testset-{timestamp}.json"
write_dict_to_json(test_set, filename)
