# Email scams: overview

Email is the oldest and most formal channel for scam communication. Email scams range from clumsy "Nigerian prince" letters to sophisticated business email compromise (BEC) that impersonates executives and vendors.

## Scale and stakes

Email is where the money is: invoice fraud, payroll diversion and CEO fraud are the highest-value scam categories, often running into lakhs or crores per incident. Unlike SMS, email allows long, formatted messages that can look extremely professional.

## Common email scam families

1. **Invoice / payment fraud** - fake invoices, fake vendor payment updates.
2. **Account verification** - "confirm your identity or your mailbox is closed".
3. **CEO/executive impersonation** - urgent payment requests from a "director" email that is a lookalike domain.
4. **Tax/refund phishing** - fake government refunds and tax notices.
5. **Stone-age classics** - lottery inheritances and stranded travelers asking for funds.

## Email-specific red flags

- Sender domain differs by one character from the real organization (amaz0n.com, bankofindia-update.com).
- Reply-To address is different from the From address.
- Attachments with macros (.docm, .xlsm) or executable files.
- Links that disagree with the visible text: the button says "icicibank.com" but the href points elsewhere.
- Poor grammar and generic salutations in supposedly corporate mail.

## How TextShield handles email

The email input type extracts the sender address and subject before analysis. The sender domain is run through the URL pattern analyzer, subject and body are combined into one text block for the ML classifier, and indicators are collected from both. The RAG layer pulls documentation about the matching scam family to strengthen the evidence for the final explanation.