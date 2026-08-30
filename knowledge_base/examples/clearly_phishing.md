Title: Clearly Phishing Example
Category: examples
Summary: Example of phishing email mimicking bank login page.
Original Message: "Subject: URGENT - Your Account Will Be Suspended Sent: justnow@fake-bank-security-alert.com Dear Customer, We have detected unusual activity on your account. To prevent suspension, please verify your identity immediately by clicking the link below. http://secure-bank-verify.com/login YOUR ACCOUNT WILL BE CLOSED IF NOT VERIFIED WITHIN 2 HOURS. - Fake Bank Security"
Expected Intent: Credential theft and account compromise
Expected Behavior: Victim enters credentials on fake login page; scammer gains account access
Expected Manipulation: Fear (account suspension), Authority (claimed bank), Urgency (2-hour deadline)
Reasoning: Message creates artificial urgency with account closure threat; uses fake domain (fake-bank-security-alert.com); generic greeting "Dear Customer" instead of name; link leads to non-official site; pressure to act within 2 hours; classic phishing pattern
Expected Risk: High - credential phishing attack