Title: OTP and Authentication Messages
Category: legitimate
Subcategory: banking
Summary: Genuine one-time-password and login-alert messages sent by banks and services after a user-initiated action.
Description: Authentication messages contain a numeric code valid for a few minutes, the service name, and an explicit warning never to share the code. They never include links asking the user to enter the OTP, never ask the user to forward the code, and arrive immediately after the user requested them.
Typical Scenario: "Your OTP is 482916" or "Login attempt from new device" or "UPI collect request verification code" or "Password reset code"
Intent: Authenticate a user-initiated session
Behavior: User enters the code only in the official app or site they opened themselves
Manipulation Techniques: None (user-initiated second factor)
Common Indicators: Sender ID of the bank or service; code validity window stated; do-not-share warning; no clickable link; no request to forward the code; arrives right after user action
Legitimate Alternatives: None - this is the legitimate communication itself
False Positives: Real OTPs flagged because they contain "urgent", "verify" or "do not share"
False Negatives: Users ignoring real login-attempt alerts
Real-world Examples: "HDFC Bank OTP 482916", "Google verification code", "UPI registration OTP", "IRCTC login code"
References: RBI Two-Factor Authentication Guidelines; CERT-In Advisories
Tags: [otp, legitimate_communication, authentication, banking]
Version: 1.0
Last Updated: 2026-09-09
Source Credibility: Banks, regulated services
Language: en-US
Confidence: 0.98
