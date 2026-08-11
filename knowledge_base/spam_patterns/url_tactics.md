# URL tactics used by spammers

Links are the delivery vehicle of almost every online scam. Spammers use a set of reproducible URL tricks that a static analyzer can detect.

## Trick 1: Shortened URLs

Services like bit.ly, tinyurl.com, t.co and goo.gl hide the real hostname. A message from a brand almost never uses a shortener; a phishing message almost always does. A shortened URL is therefore a warning sign, especially combined with urgent or reward language.

## Trick 2: Raw IP addresses

https://185.220.101.5/login is a red flag: real organizations use domain names. Raw IP hosts are typical of disposable scam infrastructure.

## Trick 3: Lookalike domains

- punycode/IDN homoglyphs: xn--pypal-4ve.com looks like paypal.com
- character substitution: paypa1.com, paypal.com, amazon-secure.com
- brand-plus-suffix: gmail-verify.com, icici-support.net, bankofindia-update.com
- extra hyphenation: e-bay-shop.com

## Trick 4: Suspicious top-level domains

TLDs such as .xyz, .top, .click, .gift, .zip, .win, .icu and .country are cheap (often free) and heavily used by bulk spammers. A .bank or .gov domain is practically impossible for a scammer to register; a .xyz domain costs nothing.

## Trick 5: Sensitive path keywords

Phishing URLs route victims to pages with words like login, verify, secure, account, update, confirm, wallet, billing, otp. These words in the path of an unknown domain are suspicious; in the path of the real domain (e.g. icicibank.com/login) they mean nothing.

## Trick 6: Suspicious characters and encoding

- '@' inside the host (http://bank.com@evil.net)
- many consecutive dots or dashes
- URLs with percent-encoding obfuscation

## Important limits of static analysis

Static analysis cannot prove a URL is malicious; it can only report suspicious patterns. Safe handling: do not click links in unsolicited messages, hover to inspect the real domain, and type known addresses manually. TextShield only performs this static analysis and never fetches the URL.