Title: Urgency and Deadline Pressure Attacks
Category: attack_patterns
Summary: Attackers compress decision time with deadlines, countdowns, and final warnings to block verification.
Description: Urgency attacks pair a threat or reward with a short fuse: suspension in hours, expiry tonight, last notice. The mechanism is identical across KYC, courier, refund, and lottery scams. Legitimate deadlines arrive with reference numbers, prior notices, and working-day timelines.
Typical Scenario: "Verify within 2 hours" or "Offer ends tonight" or "Final warning before closure"
Purpose: Detect time-pressure as an attack primitive across scam families
Detection Signals: hour-scale fuse; consequence tied to the fuse; no prior notice; no reference number; pressure repeated across sentences
Legitimate Uses: Genuine OTP windows and published offer terms with comparison time
Examples: "KYC 2-hour warning," "Parcel destruction threat," "Lottery claim deadline"
Risk Level: High - urgency is the most reused attack primitive
References: APWG Phishing Trends; CERT-In Advisories
Tags: [urgency, attack_pattern, time_pressure, coercion]
Version: 1.0
Last Updated: 2026-09-10
Source Credibility: APWG, CERT-In
Language: en-US
Confidence: 0.95
