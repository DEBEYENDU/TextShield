# Fake payment and refund scams

Fake payment and refund scams manipulate the money flow itself: they ask you to pay into a stranger's account, or claim they owe you money and need 'details to send it'.

## Variant A: advance payment fraud

The victim is asked to pay something small *before* receiving a product, job, loan or prize:

- "Pay the processing fee to receive your approved loan."
- "Confirm your parcel with a Rs.35 redelivery charge."
- "Registration fee of Rs.999 unlocks your work-from-home kit."
- "Transfer the customs/delivery/insurance charge first."

Legitimate flows never require advance payment to a private account for a service you did not order.

## Variant B: refund phishing

The scam claims money is owed to you and asks for details to 'send' it:

- "Refund of Rs.4,200 pending. Confirm your bank account and OTP."
- "Unclaimed balance in your wallet will expire - transfer it out now."
- "Your tax refund is approved. Verify through the link."

The 'verification' collects account numbers and OTPs, and several variants instead *reverse* the flow: the victim is convinced the scammer accidentally sent more than owed and is asked to 'return' the difference - money the victim themselves sent from their own account.

## Variant C: fake payment confirmation

Fraudulent "payment received" notifications attach a fake receipt and ask the victim to reconcile/ship goods or re-verify payment details - a setup for goods fraud and credential theft.

## Detection notes

TextShield scores money movement requests (pay, transfer, deposit, fee, refund) as a financial/payment indicator. When a payment request is combined with a reward promise, a loan offer or a delivery story, the risk engine classifies the message HIGH. The core rule for the explanation layer: money instructions in unsolicited messages are always suspect until verified through official channels.