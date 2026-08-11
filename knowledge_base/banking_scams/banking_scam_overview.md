# Banking scams: overview

Banking scams impersonate banks to steal money directly or to harvest credentials for later theft. They are the highest-stakes category of spam because they target the victim's entire savings.

## Attack families

1. **Account blocking** - "Your account is suspended. Call this number within 1 hour." The call center then 'confirms identity' by asking for card number, CVV, and OTPs - everything needed to transfer money out.
2. **Card incidents** - card expired, card blocked after "many failed attempts", card upgrade requiring card details.
3. **KYC/verification** - UPI, Aadhaar-linked KYC expired; update via link. The fake KYC page harvests documents and OTPs.
4. **Refunds** - bogus refunds and "cashback" requiring account details and OTP to receive.
5. **Loan offers run by banks** - official-looking instant-loan offers with processing fees paid to private accounts.

## Why bank impersonation is effective

- People fear bank problems more than any other financial issue.
- Bank notifications are frequent, so a fake one blends into the stream.
- The messages name real banks and real scheme names (UPI, Aadhaar, KYC), which feel authoritative.
- The urgency verbs ("blocked", "suspended", "deactivated") trigger immediate action.

## The universal defensive rule

A bank will never: ask for your OTP, ask for your card PIN/CVV, ask you to transfer money to "activate" anything, or direct you to a page reached from an SMS/email link. When in doubt, hang up / do not click, and call the number printed on the back of your card or the bank's official website.

## Detection notes

Banking vocabulary (card, account, KYC, UPI, Aadhaar, netbanking) is scored as high-severity by the indicator engine, and the risk engine adds extra weight for banking-derived RAG evidence. Banking scam messages compounded with links, urgency and credential requests consistently rate HIGH under TextShield's risk scheme.