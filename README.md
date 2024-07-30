# ChatLingual: An Interactive, Personalized Language Tutor Powered by GPT-4

## Project Introduction
ChatLingual is an innovative project that leverages GPT-4 to create an accessible, interactive, and personalized language tutor. The goal is to overcome the limitations of traditional language learning resources by providing a more dynamic and engaging learning experience.

## Problem Statement & Motivation
Despite the abundance of language learning resources available, several limitations persist:

1. **One-Directional Learning**: Traditional resources like textbooks and online video courses do not provide feedback on speaking or writing outputs.
2. **Limited Variation and Interaction**: Pre-set materials lack flexibility and fail to engage learners based on their interests.
3. **Lack of Customizability**: Interactive tools such as Duolingo have limited customization options and repetitive content.
4. **Financial and Scheduling Constraints**: Personal language tutors can be costly and require schedule adjustments from both parties.

The emergence of ChatGPT, with its capabilities in sentence generation, instruction following, and feedback provision, offers a new approach to language learning comparable to personal tutoring. ChatLingual aims to address these challenges by focusing on accessibility, interactivity, and personalization.

## Project Overview
ChatLingual offers three modes: **learning**, **conversation**, and **review**. Users can learn new grammar and vocabulary, practice through conversation, and review learned materials. A user profile database ensures continuity and personalized learning experiences.

## Python Version: 
3.11

## Instructions to Run
#### Install the virtualenv package if it's not installed
```
python -m pip install --user virtualenv
```

#### Create a virtual environment in the project directory
```
python -m venv venv
```

#### activate venv
```
source venv/bin/activate
```

#### install all requirements
```
pip install -r requirements.txt
```

#### run the main program
```
cd LanguageTutor_v1
python3 app.py
```


## Functionality
### Learning Mode
**Functionality**: Introduces new grammar and vocabulary at the user's target difficulty level. Provides explanations, examples, and role-playing exercises. Supports both audio and text inputs/outputs.

**Implementation**: Utilizes a LearningKani built with the Kani framework. The system prompt outlines the steps to teach each grammar point, including examples and role-playing activities. 

### Conversation Mode
**Functionality**: Facilitates back-and-forth conversations to practice listening and speaking skills. Topics are based on the user’s interests, past discussions, or user-specified topics. The mode defaults to audio interactions to simulate real-world conversations.

**Implementation**: Uses a ConversationKani with modules for grammar detection, vocabulary detection, sentence tokenization, and sentence simplification. The system prompt provides guidelines for conversation flow and difficulty level.

### Review Mode
**Functionality**: Allows users to review and practice learned grammar and vocabulary through role-playing prompts that synthesize multiple concepts. Items mastered through repeated correct usage are tracked in the user profile.

**Implementation**: Rolling out review mode with features to integrate spaced repetition and role-playing formats.

### Language Database
The language database is structured around widely-recognized proficiency levels for each supported language (e.g., JLPT for Japanese, CEFR for multiple languages). Content is web-scraped from popular exam-preparation websites and stored as JSON files.

### Example JSON Format:
```json
"のが好き（のがすき）": {
  "meaning": "to like doing something",
  "level": "n5"
}
```
### User Profile
Each user has a personal profile stored as `<username>.json`, containing information such as the user’s name, language of study, interests, past discussion topics, and learning progress. This ensures personalized and up-to-date interactions across all modes.

## Features & Modules

### Speech to Text
**Functionality**: Transcribes user audio input to text using OpenAI’s Whisper-1 model. The text is then fed into the main model as user input.

### Text to Speech
**Functionality**: Converts the text output of the main model into audio using OpenAI’s TTS-1 model. The audio is played in the browser.

## Challenges & Solutions

### Limiting Difficulty Level
Multiple approaches were explored to control the difficulty level of model outputs, including prompt engineering, utilizing a "to-use" list, and programmatic checks through external modules (Grammar Detector, Vocabulary Detector, Sentence Tokenizer, Sentence Simplifier).

### Grammar and Vocabulary Detection
Implemented detectors to identify grammar points and vocabulary from the model’s output that are beyond the user's current level, ensuring appropriate difficulty adjustments.

### Sentence Simplification
A GPT-4 model is used to simplify sentences by swapping out difficult expressions for easier ones, sometimes incorporating translations in the user’s backup language.

## Live Site
[Link to Live Site](#)
