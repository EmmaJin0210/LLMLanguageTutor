import os
from getpass import getpass
from openai import OpenAI


def set_api_key():
    if 'OPENAI_API_KEY' not in os.environ:
        print("You didn't set your OPENAI_API_KEY on the command line.")
        os.environ['OPENAI_API_KEY'] = getpass("Please enter your OpenAI API Key: ")
    return os.environ['OPENAI_API_KEY']


def construct_user_prompt(language, level, category="grammar point"):
    # Probably few-shot prompt it with existing human-written guidelines
    prompt = f"Generate a comprehensive list of {category}s needed for {level} level {language}."
    prompt += f"List each {category} in {language}. Generate the list in a concise, bullet-point format."
    prompt += f"You can inlcude short explanations for what each {category} means, but no need to include pronunciation."
    prompt += "Make the list as comprehensive as possible."
    return prompt

def get_system_prompt():
    prompt = "You are a helpful guideline generator for students studying different languages."
    return prompt

def generate_grammar_list(language, level):
    system_prompt = get_system_prompt()
    user_prompt = construct_user_prompt(language, level)
    client = OpenAI()

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    with open("grammar.txt", "w") as file:
        file.write(completion.choices[0].message.content)

def generate_vocab_list(language, level):
    system_prompt = get_system_prompt()
    user_prompt = construct_user_prompt(language, level, "vocab")
    user_prompt += "Generate the list in the format of <index>. <word>: <explanation>."
    user_prompt += "Only generate the list and nothing else."
    client = OpenAI()
    # how many words are there in xx?
    num_of_words_prompt = f"How many words are needed for {level} {language}? Answer an integer. For example, 2000"
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": num_of_words_prompt}
        ]
    )
    num_words = int(completion.choices[0].message.content)
    print("num_words: ", num_words)
    # if not to the length of half those words (number of lines), keep generating
    target_num = num_words // 4
    curr_num_words = 0
    messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    messages += [completion.choices[0].message]
    content = completion.choices[0].message.content
    lines = content.splitlines()
    print(lines)
    cutoff_index = len(lines) - 1
    for i in range(len(lines) - 1, -1, -1):
        to_check = lines[i].strip().split('.')[0]
        print(to_check)
        if to_check.isdigit():
            cutoff_index = i
            break
    lines = lines[:cutoff_index+1]
    num_words = cutoff_index + 1
    curr_num_words += num_words
    with open("vocab.txt", "a") as file:
        for line in lines:
            file.write(line)
            file.write('\n')
    while curr_num_words < target_num:
        print("curr_num_words: ", curr_num_words)
        messages += [{"role": "user", "content": "Generate more words."}]
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        messages += [completion.choices[0].message]
        content = completion.choices[0].message.content
        lines = content.splitlines()
        print(lines)
        cutoff_index = len(lines) - 1
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().split('.')[0].isdigit():
                cutoff_index = i
                break
        lines = lines[:cutoff_index+1]
        num_words = cutoff_index + 1
        curr_num_words += num_words
    with open("vocab.txt", "a") as file:
        for line in lines:
            file.write(line)
            file.write('\n')


def main():
    my_key = set_api_key()
    language = "Japanese"
    level = "JLPT N4"
    generate_grammar_list(language, level)
    generate_vocab_list(language, level)




if __name__ == "__main__":
    main()