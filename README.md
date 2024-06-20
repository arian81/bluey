# BlueBot: Discord Waitlist Queue for Bluesky Invites

A Discord bot built with py-cord and SQLAlchemy that manages a waitlist queue for Bluesky invites on [Blue Social Discord Server](https://discord.com/invite/bluesky-social-1100501016090267749). The bot prioritizes users based on their message activity and other engagement metrics determined by admins.

## Features:
- Track user activity in Discord servers
- Maintain a dynamic waitlist queue
- Distribute Bluesky invites automatically
- Customizable scoring system for user prioritization

## Tech Stack:
- Python
- py-cord (Discord API wrapper)
- SQLAlchemy (ORM for database management)
- PostgreSQL

## Getting Started:
1. Clone the repository:
```sh
git clone https://github.com/arian81/bluey
cd bluey
```
2. Install dependencies using pipenv:
```sh
pipenv install
```
3. Create a `.env` file in the project root and add your Discord bot token:
```sh
DISCORD_BOT_TOKEN=your_bot_token_here
```
4. Activate the virtual environment:
```sh
pipenv shell
```
5. Run the bot:
```sh
python main.py
```
## License:
* License: MIT


