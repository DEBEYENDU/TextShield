# SMS scams: overview (smishing)

Smishing is phishing delivered by SMS. SMS has special properties that scammers exploit: short length, sender IDs that are easy to fake, high trust in mobile notifications, and little space for the recipient to verify details.

## Why SMS targeting works

- SMS arrives with "notification status" - people read it as system communication.
- Text is short, so urgency is compressed ("Your card is blocked. Call now").
- Sender IDs can be spoofed to show a bank or brand name.
- No spam filter by default on plain SMS gateways.

## Main smishing categories

1. **KYC/Aadhaar updates** - "Aadhaar unlinked, update via link" - fake KYC portals steal documents and OTPs.
2. **Bank blocking** - "Account suspended, verify immediately" - fake verification pages harvest credentials.
3. **Lottery/prize wins** - "You have won Rs.50,000" - advance-fee fraud.
4. **Delivery customs** - "Your parcel is stuck, pay the customs fee" - small payments to fake couriers.
5. **SIM/number expiry** - "Your SIM will be deactivated today" - drives calls to scam call centers.
6. **Loan offers** - "Instant loan, no documents" - processing-fee fraud.

## Behavior patterns of smishing campaigns

- Heavy use of "Dear customer" generic address
- Links with shorteners or single-use domains
- Barely-concealed threats (blocked, cancelled, fined)
- Requests for OTP/PIN - the confirmed giveaway
- Odd phone numbers and toll-free numbers posing as support

## Detection strategy

SMS messages are short, which makes TF-IDF features sparse - exactly why TextShield combines ML with indicator rules, URL analysis and RAG context. A short message with a link, a reward claim and urgency gets flagged by all layers at once, which compensates for the scarcity of text.