# Safety guidelines: checking URLs safely

URL verification is the single most practical skill against phishing. This checklist explains how to inspect a link without ever clicking it.

## 1. Reveal the destination without clicking

- On desktop, hover the mouse over the link; the real URL appears in the status bar / tooltip.
- On mobile, long-press the link; the destination is previewed before you release.
- In email clients, the 'View original' option shows the raw HTML href - compare it with the visible button text. Phishing often shows a real-looking label over a different href.

## 2. Read the domain, not the text

The only authority is the hostname (the part right of the //):

- Correct: paypal.com, icicibank.com, government portal domains ending .gov.in
- Lookalike: paypa1.com, paypal-security.com, icici-bank-update.xyz, xn--paypal-xyz domain clones
- Ask: "would the real organization send me a link whose domain I have never seen?"

## 3. Check the visible red flags

- Shortened domain (bit.ly, tinyurl.com, t.co) in a message from a brand - brands do not hide their links
- Raw IP address instead of a domain
- Cheap/unusual TLD: .xyz, .top, .click, .gift, .zip, .win, .icu, .rest
- '@' inside the address, excessive dashes, punctuation in the host
- Path keywords pointing at login/verify/update/security pages on an unknown domain

## 4. What TextShield can and cannot do

TextShield performs static URL pattern analysis only: it can report suspicious patterns (shorteners, IP hosts, lookalike structure, unusual TLDs, sensitive path words), but it does not fetch the URL and cannot certify safety. A URL that triggers no pattern warning is still not guaranteed safe - unknown content cannot be judged from structure alone.

## 5. The rule that never fails

Type the important addresses yourself. Bank, government, courier - open the official site directly in the browser. If an emailed/SMS link simply 'saves you time', the time saved is exactly what the phisher is monetizing.