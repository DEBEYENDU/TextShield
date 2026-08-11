# OTP fraud

OTP (one-time password) fraud targets the last line of defense of online banking: the verification code sent to your phone. Once an attacker obtains an OTP, they can complete transactions or reset passwords.

## Why OTP scams work

- Banks, genuinely, never ask you to share an OTP - the code exists precisely because it must stay secret.
- Scammers create believable cover stories: fake customer care, KYC updates, cashback claims, or "fraud alert" calls.
- Victims read fast, panic, and repeat the six digits.

## OTP scam message patterns

- "Your OTP is 482913. Do not share this with anyone." (the genuine message, which scammers use as proof)
- "Share the OTP received to complete your refund."
- "Our executive will need the OTP to block your compromised card."
- "KYC verification requires the OTP sent to your mobile."

## Hard rule

**Never share an OTP with anyone, on any call, for any reason.** No company employee, executive, or official will ever ask for it. Any message that requests OTP submission or conducts a transaction "where OTP is shared" is fraudulent.

## Detection notes

The presence of OTP/verification-code vocabulary in a message is flagged by TextShield's indicator engine as a high-severity credential signal, and any message instructing the user to share an OTP is treated as hostile even when the surrounding text is calm.