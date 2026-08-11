# Example spam messages (unlabeled examples for retrieval)

The following are representative spam messages across scam families. They are used as retrieval examples: when a new message resembles one of these, the RAG system returns it as evidence of similarity.

- "Congratulations! You have won a cash prize of Rs.50,000. Click here to claim your reward now."
- "HURRY UP! LIMITED TIME OFFER! Get 90% discount on all electronics. Visit our website today only."
- "Dear customer, your Airtel number will be blocked tonight. Click the link to update your KYC immediately."
- "Your bank account has been suspended due to suspicious activity. Verify your account within 24 hours using this link."
- "WINNER! You have been selected for a free iPhone 15 Pro. Claim your gift within 1 hour."
- "Earn Rs.50,000 per month from home. No experience required. Pay Rs.999 registration fee to start today."
- "Your parcel is stuck at the courier office due to unpaid delivery charges. Pay Rs.35 to reschedule delivery now."
- "Get an instant loan of up to Rs.5,00,000 without any documents. Low interest, no CIBIL check. Apply now."
- "Your UPI has been blocked. Click to verify your identity and avoid permanent deactivation."
- "Your OTP is 482913. Do not share this code with anyone."
- "Congratulations! You have won a free luxury watch. Pay only the shipping fee of Rs.499."
- "Your Netflix account is suspended. Sign in to update your payment details and continue watching."
- "Buy one get one free on all perfumes this weekend only! Hurry, stock limited. Call 9876543210 now."
- "Double your money in 30 days with our guaranteed crypto trading signals. Invest now and become a crorepati."
- "Your electricity bill payment has failed. Pay the outstanding amount now or your connection will be cut."
- "Work from home opportunity: type simple documents and earn daily salary. Register with Rs.500 only."
- "Your bank account has been credited with Rs.10,000 as refund. Click here to confirm your details."
- "Last warning! Your SIM card will be deactivated in 2 hours. Verify your details now to continue."
- "Your Flipkart order could not be delivered. Update your address through the link to receive your package."
- "Paytm KYC pending! Your account will be blocked tomorrow. Complete KYC instantly through this link."

These examples are curated for demonstration. In production, similarity search over such labeled examples gives analysts a quick "this looks like known scam X" hint, while the ML classifier remains the primary decision maker.