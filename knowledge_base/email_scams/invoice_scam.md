# Invoice and payment fraud

Invoice fraud sends fake invoices that look like bills from real vendors, service providers or tax authorities, hoping the receiver will pay without verification.

## Typical invoice scam templates

- "Your electricity bill payment failed. Pay now of you will be disconnected." (note the grammar mistake - genuine bills are carefully worded)
- "Dear customer, your new invoice is attached. Amount due: Rs.4,250."
- "Unpaid balance on your account - late fee of Rs.500 will apply after today."
- "Tax refund pending: your unclaimed refund of USD 3,400 requires bank verification."
- "Your magazine/software subscription renews automatically tomorrow. Cancel here to avoid charges."

## The psychology

1. **Authority** - invoices come from "the billing department" with technical-looking numbers.
2. **Anchoring** - the payee compares the amount to their normal bills; a similar-looking amount passes the mental check.
3. **Fear of penalty** - disconnection, late fees and legal threats force rapid payment.
4. **Busy targets** - professionals processing many payments click through familiar-looking invoices.

## Safety checks

- Verify the sender domain on every invoice email, not just the display name.
- Check the paying account: legitimate vendors do not change bank details without a phone call.
- Never open invoice attachments you did not expect.
- For government-bill messages, use the official app/portal to check dues instead of the link in the message.

## Detection notes

Invoice scams score high in the indicator engine: payment language + urgency + a link. When the "organization" is a bank or utility and the message demands immediate payment, the risk engine marks the message HIGH. The RAG layer assists by retrieving documentation on payment-fraud patterns for the explanation.