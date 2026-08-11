# Spam patterns: overview

Spam is any unsolicited, often promotional or fraudulent message sent in bulk. Spam messages across SMS, email and chat platforms share a surprisingly small set of recurring patterns. Understanding these patterns is the core of rule-based spam detection.

## Common structural patterns

1. **Call to immediate action** - spam almost never asks you to think; it asks you to click, call, or reply right now. Time-pressure language such as "act now", "limited time", "offer expires today" and "hurry" is a strong spam signal.
2. **Reward without effort** - prizes, cash rewards, free gifts, lucky draws and lottery wins that you never entered. Legitimate organizations do not give away large prizes to random phone numbers.
3. **Fee before reward** - the scam asks you to pay a small "processing fee", "shipping fee", "registration fee" or "tax" before you can receive the promised reward. Real promotions never charge you to receive a prize.
4. **Generic addressing** - spam addresses "Dear customer", "Dear user" or "Sir/Madam" instead of your name, because the message is blasted to millions of recipients.
5. **Links and shortened URLs** - spam relies on links to phishing sites, malware downloads or fake login pages. Shortened URLs (bit.ly, tinyurl, t.co) hide the true destination.
6. **Emotional triggers** - fear (account will be blocked), greed (free money), excitement (you won!) and urgency are deliberately engineered emotions.

## Why patterns matter in detection

Machine learning classifiers learn these patterns from labeled examples, while a rule-based indicator engine matches them directly. Neither approach alone is perfect: ML generalizes to unseen phrasings, rules provide explicitly explainable evidence. The best systems combine both, which is exactly the TextShield architecture.

## A caution

Some legitimate marketing messages also contain urgency or rewards. Pattern detection reports *possible* signals, not proof of fraud. Always judge a message by its whole context: known sender + no requests for credentials + verifiable contact points means the risk is low even when marketing language is present.