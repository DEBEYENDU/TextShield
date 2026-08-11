# "Account blocked" scam

"Your bank account will be blocked" is the most widely used banking scam opener. It combines the strongest fear trigger (losing account access) with fake authority.

## Script outline

1. **Trigger** - "Your account has been suspended due to unusual activity / failed KYC / fraudulent use."
2. **Funnel** - "Call 1800-xxx immediately" or "Verify through this link."
3. **Bait** - "Our officer will help unlock the account - have your card and aadhaar ready."
4. **Harvest** - the 'officer' asks for card number, expiry, CVV, and finally the OTP that enables the transfer.

## Why it is always fake

Real banks do not block accounts and then demand full card details from SMS links or unsolicited calls. Even during genuine KYC drives, banks ask you to visit the branch or use the official app. An SMS demanding you "call now before your account is blocked" is a script, not an alert.

## Detection flags in TextShield

- blocked/disabled/suspended account wording (high severity)
- verification/update link in the same message (high severity)
- call-now instructions to an unknown number (high severity)
- KYC + Aadhaar + deadline language (high severity)

## Recommended action

Do not call the number. Do not use the link. Open your bank's official app, and if the account looks fine (it will), report the message to the bank's official helpline. Blocking/ignoring is the correct response, and helping relatives recognize the pattern is the best defense.