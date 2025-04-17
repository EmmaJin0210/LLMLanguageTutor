APP_IP = "127.0.0.1"
APP_PORT = 8000
SERVER_ADDR = f"{APP_IP}:{APP_PORT}"

MOUNT_TEMP_DATA = "/temp-data"
MOUNT_STATIC = "/static"

ROOT_TEMP_DATA = "LanguageTutor_v1/appstuff/tempdata/"
ROOT_STATIC = "LanguageTutor_v1/appstuff/web_ui/static/"
ROOT_USER_PROFILES = "LanguageTutor_v1/db/user_profiles/"
ROOT_TEMPLATES = "LanguageTutor_v1/appstuff/web_ui/templates/"
ROOT_STATIC_DB = "LanguageTutor_v1/db/static_database/"

FILENAME_USERS_DB = "all_users.json"
FILENAME_AUDIO_INPUT = "input.wav"
FILENAME_AUDIO_OUTPUT = "output.wav"
FILENAME_PROFILE_TEMPLATE = "<username>.json"

MSG_PROGRESS_SAVE_SUCCESS = "Progress saved! Your learning and conversation sessions hereon will \
    take into account what you learned today.\n\nRedirecting to homepage..."
MSG_PROGRESS_SAVE_FAIL = "Failed to save progress..."
MSG_TRANSCRIBE_AUDIO_FAIL = "Failed to transcribe audio..."