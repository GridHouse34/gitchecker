# gitchecker
A bot meant to communicate changes on your profile to Discord!

The GitChecker bot is meant for mostly automating the process of changes to a GitHub profile. It's simple, self-hostable, and made in .py, meaning it's relatively easy to configure should there be need to do it.

INSTALLATION:
-----------------------
The bot has multiple requirements, both for the code and to deploy.
I recommend installing Python 3.12 to not get in trouble with audioop package - it doesn't exist on newer versions.

▶️ HOW TO RUN
1. Create and activate venv
python3.12 -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

2. Install dependencies
pip install -r requirements.txt

3. Create .env and place the following text in there:
DISCORD_TOKEN=[DISCORD_BOT_TOKEN]
GITHUB_USERNAME=[GITHUB_USER]
GITHUB_TOKEN=[FINE_GRAIN_TOKEN]  
DEFAULT_CHANNEL_ID=0                 # can be changed with !channel
CHECK_INTERVAL=3600                  # default: 1 hour or 3600 seconds

3.1 Getting your tokens for the bot
Go to Discord Developer Hub and make an application. Then, under Bot, reset its token and copy it into the .env.
The GitHub username can be found in the URL when checking your profile.
The GitHub token can be found under Settings> Developer Settings> Personal Access Tokens and Fine-grained tokens. Make sure it can read public repos.

4. Run bot
python bot.py
