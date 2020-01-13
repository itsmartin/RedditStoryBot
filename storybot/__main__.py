#!/usr/bin/env python
from . import StoryBot
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='A reddit bot for story-based subreddits')
parser.add_argument("--post", action="store_true",
                    help="If specified, the bot will post to reddit; if omitted, it will only output what would been posted.")
parser.add_argument("config_file", type=Path, help="The YAML configuration file")

args = parser.parse_args()

bot = StoryBot(post_mode=args.post, config_file=args.config_file)
bot.run()
