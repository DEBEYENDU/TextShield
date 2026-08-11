# Account verification scam

The account verification scam impersonates service providers - email hosts, banks, social networks, payment apps - and insists that an account action is needed "to keep your account safe".

## Common variants

- "Your account will be permanently deleted in 24 hours unless you verify your email."
- "Suspicious sign-in detected. Confirm it was you, otherwise your account is locked."
- "Your account has exceeded its storage limit. Upgrade to avoid suspension."
- "We are updating our security policy. Re-authenticate through this secure link."
- "Your account has been flagged for unusual activity. Verify now."

## How victims are funneled

The message points to a fake login page that is a pixel-perfect copy of the real one. When the victim "logs in", credentials go directly to the attacker. Then the attacker either uses those credentials or performs a password reset and takes over the account entirely.

## Detection indicators

- Generic greeting ("Dear customer") instead of the account name
- A "secure link" whose real host is not the provider's domain
- Punctuation and phrasing slightly off for the impersonated brand
- The implied deadline (24 hours, end of day) - real providers send no such deadlines

## Action guidance

Never click verification links in messages. For any account concern, open the service directly in your browser (type the address yourself) or use the official mobile app. A verification request that arrives through a message is, in the overwhelming majority of cases, the attack itself.