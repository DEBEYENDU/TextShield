# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.2.x   | :white_check_mark: |
| 2.1.x   | :white_check_mark: |
| < 2.1   | :x:                |

## Reporting a Vulnerability

Please do NOT open public issues for security vulnerabilities.

Email security reports to: debeyendukarmakar@gmail.com

Include:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix if known

We will acknowledge receipt within 5 business days and provide a remediation timeline.

## Security Considerations

- No secrets in source; use `.env`
- All external input validated via Pydantic
- URL analysis is static; no network fetches
- LLM is explain-only; never overrides ML verdict
- History stores SHA-256 hashes by default
- Logs redact API keys and message bodies

See README Security Considerations section for details.
