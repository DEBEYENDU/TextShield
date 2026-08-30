Title: Ambiguous Example
Category: examples
Summary: Example of ambiguous communication - unsolicited message about account verification.
Original Message: "Subject: Account Verification Required Sent: verification@secure-netflix-alert.com Dear User, Your Netflix account needs verification to maintain access. Click here to verify your account now. http://verify-netflix-account.com Failure to verify within 24 hours will result in permanent account deletion."
Expected Intent: Mixed - could be legitimate verification request or phishing for Netflix credentials
Expected Behavior: Victim may click link and enter credentials, or realize it's fake
Expected Manipulation: Fear (account deletion), Authority (claimed Netflix), Urgency (24-hour deadline), Personalization (generic "User")
Reasoning: Message uses Netflix branding and context; generic greeting "User" rather than name; domain is slightly altered (secure-netflix-alert.com); urgency with 24-hour deadline; could be legitimate Netflix verification request or phishing - depends on whether recipient recently initiated verification and recognizes official Netflix communication channels
Expected Risk: Medium - ambiguous between legitimate service notification and credential phishing