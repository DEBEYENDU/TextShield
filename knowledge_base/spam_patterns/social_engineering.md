# Social engineering fundamentals

Social engineering is the manipulation of people into performing actions or revealing information, and it is the beating heart of every scam category in this knowledge base. Understanding the psychology explains why the same templates work decade after decade.

## The six principles exploited by scammers

1. **Urgency** - deadlines and threats short-circuit reasoning ("your account will be blocked in 2 hours").
2. **Authority** - impersonated banks, police, tax offices and brands transfer legitimacy ("RBI notices...", "court fine").
3. **Scarcity / reward** - "only 2 winners", "limited time", "free gift" trigger greed and fear of missing out.
4. **Consistency** - once a victim sends small money or shares minor data, they tend to comply further ("we already started the process, just one more step").
5. **Social proof** - "thousands have already claimed", fake screenshots of withdrawal confirmations, fake WhatsApp groups of 'happy investors'.
6. **Liking** - romance scams, friend-in-need messages and 'executive' flattery lower defenses.

## The scam funnel

Pretext (fake identity/story) -> trust building (fake proof, calm tone) -> small request (harmless-looking) -> escalating requests (fees, OTP, documents) -> extraction (money, data, account takeover) -> ghosting (or continued extraction).

## Why detection must be multi-layered

Because social engineering adapts its wording infinitely, no single technique suffices:

- a lexical classifier (ML) learns familiar scam phrasings and generalizes;
- a rules engine (indicators) pins down structural tells (urgency, money, links);
- URL analysis catches the infrastructure (shorteners, lookalikes);
- RAG retrieval matches the message against written scam knowledge for evidence;
- an LLM summarizes all layers into a human-readable explanation.

Each layer is fallible in isolation; together they produce a defensible risk estimate that humans can inspect, which is exactly the promise of an explainable spam-detection system.