# Credential phishing

Credential phishing targets passwords, PINs, MPINs, OTPs and security answers. It is among the most damaging scam categories because leaked credentials grant direct account access.

## Typical message templates

- "Dear user, your account password expires today. Log in at [link] to keep the same password." - no service makes you log in over an email/SMS link to "keep" a password.
- "Your payment failed. Confirm your card details (including CVV) to retry." - services never ask for the CVV by message.
- "Enter your current password to verify your identity." - a genuine request for your current password from an unsolicited message is a hostage negotiation with your own account.
- "Your OTP will expire in 2 minutes. Share it with our support to complete verification." - sharing an OTP with anyone is exactly how accounts get drained.

## Why requesting any credential is a scam

Legitimate organizations never ask for passwords or OTPs through unsolicited SMS, email, or phone calls - they already have these records. Whenever a message asks you to *type, share, send or confirm* a password, PIN, OTP or CVV, treat the message as hostile regardless of everything else in it.

## Detection indicators in TextShield

- password/pin/mpin login credential phrases
- "share this OTP" and "verification code" requests
- verification/update links pointing at unknown domains
- combined urgency + credential request

## Recommended action

If a message requests credentials, do not respond, do not click links, and if the message impersonates your bank, contact the bank through its official app or the number on your card/statement.