import random
import sys

# N5: 
topics = [
    "Summer vacation plans",
    "Weekend hobbies or routines",
    "Favorite movie or TV show",
    "Favorite book, story, or folklore",
    "Favorite sport or physical activity",
    "A memorable trip or vacation",
    "A time you got sick",
    "A favorite holiday or festival",
]

# N4 / early N3
topics = [
    "A time something was stolen",
    "A time you were hurt or injured",
    "Doing house chores",
    "A habit that annoys you",
    "A time you reported a crime or accident",
    "A favor you asked from someone",
    "A time you had to say goodbye",
    "A promise or decision you made",
    "A future goal that you have",
    "A region in Japan you want to visit",
    "A famous place you’ve been to",
    "A local food or specialty you like",
    "A festival you’ve attended or want to see",
    "Your hometown and what it's known for",
    "A memorable travel story",
    "A seasonal event you enjoy",
    "A travel recommendation for a friend"
]


# N2: 
topics = [
    "Describe a recent news story you found interesting, and why it caught your attention",
    "Explain one cultural difference between Japan and your country, and how it affects communication",
    "Discuss a challenge people face when communicating in a Japanese workplace",
    "Talk about a social issue you care about and why it's important to you",
    "Describe a time you had to be polite in a difficult situation",
    "Compare education systems in Japan and your home country",
    "Share your opinion on using AI or technology in daily life",
    "Describe a tradition or custom from your country and how it's changing",
    "Talk about how your communication style changes depending on the situation",
    "Discuss the pros and cons of working remotely or studying online",
    "Talk about a piece of Japanese literature you like",
    "Discuss how Japanese society is addressing the social issue of aging population"
]




def show_three():
    """Randomly choose and print three distinct topics, one per line."""
    print("\n🗣  Choose one of these topics:")
    for topic in random.sample(topics, 3):
        print(topic)
    print()                   # blank line for spacing

def main():
    print("Press <Enter> to get three new topics, or type q and <Enter> to quit.\n")
    show_three()

    while True:
        try:
            user_input = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGood‑bye!")
            sys.exit()

        if user_input == "q":
            print("Good‑bye!")
            break
        else:
            show_three()

if __name__ == "__main__":
    main()
