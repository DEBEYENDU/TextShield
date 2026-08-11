# Promotional language patterns

Promotional language is the legal, high-volume cousin of spam: e-commerce offers, discount ads, win-back campaigns. Classifying it accurately matters because most false positives in spam detection come from aggressive marketing messages.

## Typical promotional phrases

- "Hurry! Limited period offer"
- "Flat 70% off - today only"
- "Buy one get one free"
- "Special discount for you"
- "Season sale / clearance sale / festive sale"
- "Spend and win" cashback programs
- "Exclusive offer" and "members-only deals"

## Signals that push marketing toward spam

Promotional messages become spam-like (and often are actual spam) when they add:

- **Artificial urgency** - countdown timers, "offer expires in 2 hours"
- **Surprise rewards** - "you have been selected", "you won a gift card"
- **Unknown short links** - links that do not point to the brand's real domain
- **Non-branded sender names** - text from random numbers pretending to be a brand
- **Request for payment or verification** - "pay a delivery fee to claim your free gift"

## Why this matters for detection

A message that merely advertises ("Flat 50% off this weekend") is high-promotion, low-risk: probably HAM. A message that combines promotion with urgency, a prize claim and a suspicious link is a classic spam blend. The indicator engine treats promotional language as a low-severity signal on its own, and the risk engine raises the level only when it is combined with stronger evidence.