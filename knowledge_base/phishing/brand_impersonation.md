# Brand impersonation

Brand impersonation scams pretend to be a known company - banks, telecom operators, marketplaces, couriers, government agencies - to earn trust and extract money or data.

## Methods used

1. **Spoofed sender names**: the SMS sender ID reads "AIRTEL", "ICICI" or "Amazon" but the number is random.
2. **Lookalike domains**: amazon-offers.site, icicibank-helpline.xyz, paytm-verify.top.
3. **Real-brand content, fake links**: the text mimics genuine notification style ("Dear customer, your monthly bill is ready") but the link points elsewhere.
4. **Authority abuse**: messages pretending to be the police, tax office, RBI, TRAI or court with legal threats.

## Common brand targets

- Banks (account blocked, KYC, card expiry)
- Telecom (SIM blocked, number expiry)
- Marketplaces (Amazon, Flipkart, Meesho: gift cards, delivery issues)
- Payment apps (Paytm/PhonePe wallet KYC, cashback)
- Government (Aadhaar update, PAN verification, subsidy claims)
- Couriers (FedEx, DHL, India Post: customs fees, redelivery)

## Consistency checks for humans and models

- Does the sender ID match the claimed brand?
- Does every link point to the brand's official domain?
- Is the message asking for something the brand would never ask (OTP, fee for a prize, card CVV)?
- Is it urgent *and* financial *and* from an unknown source?

## Detection notes

TextShield's URL analyzer compares link hosts against suspicious-pattern rules and flags lookalike structures ('brand-word + unusual TLD'). The risk engine raises severity when a message impersonating a known brand also requests money, credentials or clicks. Always verify through official channels, never through the message.