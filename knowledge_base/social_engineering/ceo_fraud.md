Title: CEO Fraud and Business Email Compromise
Category: social_engineering
Summary: Attackers impersonate executives to order secret, urgent wire transfers from finance staff.
Description: CEO fraud combines authority bias, secrecy, and urgency: a spoofed executive demands a confidential payment while claiming to be unreachable. Real executive payment requests follow approval workflows, never secrecy, and tolerate verification callbacks.
Typical Scenario: "Confidential acquisition, wire funds now" or "I am in a meeting, process this" or "Do not tell anyone yet"
Purpose: Detect executive impersonation patterns
Detection Signals: secrecy demand; executive unreachable; bypass of approval process; new payee; urgency tied to confidentiality
Legitimate Uses: Genuine executive requests routed through finance workflows with dual approval
Examples: "Fake CEO acquisition wire," "Spoofed MD vendor payment," "BEC payroll diversion"
Risk Level: Critical - high-value corporate losses
References: FBI IC3 BEC Reports; CERT-In Advisories
Tags: [ceo_fraud, bec, impersonation, wire_fraud]
Version: 1.0
Last Updated: 2026-09-10
Source Credibility: FBI IC3, CERT-In
Language: en-US
Confidence: 0.97
