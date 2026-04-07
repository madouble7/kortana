#!/usr/bin/env python3
"""
🐱 Distraction Script: Random ASCII Cats & Motivational Quotes
Run this to get a fun break: cute cat ASCII art and a random uplifting quote.
"""
import random
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

cats = [
    r"""  /\_/\
 ( o.o )
  > ^ <""",  # classic cat
    r""" |\---/|
 | o_o |
  \_^_/""",  # another cat
    r"""  /\_/\
 (> ‚¬ â )
  /   \"""  # quirky cat
]

quotes = [
    "Keep going, you're doing great!",
    "Every step counts, no matter how small.",
    "Believe in yourself!",
    "One line of code at a time.",
    "You make a difference.",
    "Embrace the unexpected.",
    "Code, cat, repeat.",
    "Pause and enjoy the moment."
]

if __name__ == '__main__':
    while True:
        clear_screen()
        cat = random.choice(cats)
        quote = random.choice(quotes)
        print(cat)
        print("\n" + quote + "\n")
        try:
            input("Press Enter for another dose of cute cats (or Ctrl+C to exit)...")
        except KeyboardInterrupt:
            print("\nHave a great day! 🐾")
            break
