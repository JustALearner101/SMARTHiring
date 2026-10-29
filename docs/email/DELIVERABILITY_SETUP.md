# Anti-SPAM Email Deliverability & DNS Configuration Guide

This guide details the DNS, cryptographic authentication, and RFC compliance standards implemented in the **Heketon AI Orchestrator** to guarantee interview invitation delivery directly to the recipient's **Primary Inbox** (Gmail, Microsoft 365, Yahoo, Apple Mail), eliminating SPAM/Junk placement.

---

## 1. Domain Authentication Standards (SPF, DKIM, DMARC)

Major inbox providers (Gmail, Microsoft 365) enforce strict DMARC alignment and SPF/DKIM verification for all inbound communications.

### 1.1. SPF (Sender Policy Framework) - RFC 7208
Authorizes the Heketon SMTP server IP / relay to send emails on behalf of your domain.

Add the following `TXT` record at your domain's root (`@`):

```dns
Type:  TXT
Host:  @
Value: v=spf1 include:_spf.sumopod.com include:_spf.google.com ~all
TTL:   3600
```

> **Note**: Replace `_spf.sumopod.com` with your active SMTP relay provider's SPF inclusion mechanism.

---

### 1.2. DKIM (DomainKeys Identified Mail) - RFC 6376
Signs outgoing message headers with a 2048-bit RSA private key, proving the email was not tampered with in transit.

1. Generate a 2048-bit RSA key pair:
   ```bash
   openssl genrsa -out dkim_private.key 2048
   openssl rsa -in dkim_private.key -pubout -out dkim_public.key
   ```

2. Publish the public key to DNS with selector `heketon`:
   ```dns
   Type:  TXT
   Host:  heketon._domainkey
   Value: v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
   TTL:   3600
   ```

---

### 1.3. DMARC (Domain-based Message Authentication, Reporting & Conformance) - RFC 7489
Instructs mailbox providers how to handle emails that fail SPF or DKIM checks, while collecting forensic telemetry.

Add the following `TXT` record at `_dmarc`:

```dns
Type:  TXT
Host:  _dmarc
Value: v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-reports@smarthiring.ai; ruf=mailto:dmarc-forensics@smarthiring.ai; adkim=r; aspf=r
TTL:   3600
```

| Tag | Recommended Value | Purpose |
| --- | --- | --- |
| `p` | `quarantine` (initial) → `reject` (prod) | Quarantine unauthenticated impersonators |
| `pct` | `100` | Applies to 100% of outgoing traffic |
| `rua` | `mailto:...` | Aggregate daily deliverability reports |
| `adkim` | `r` (relaxed) | Allows subdomains with matching DKIM |
| `aspf` | `r` (relaxed) | Allows envelope From relaxation |

---

## 2. Header Hygiene Implemented in Heketon

[`EmailDispatcherService.py`](file:///D:/Project/Heketon/backend/app/service/EmailDispatcherService.py) injects mandatory RFC headers on every dispatched invitation:

1. **`Message-ID`**: Formatted with unique UUID and sender domain (e.g. `<uuid@smarthiring.ai>`).
2. **`Date`**: Formatted according to RFC 2822 (`email.utils.formatdate(localtime=True)`).
3. **`Auto-Submitted: auto-generated`**: Identifies system-automated notifications and suppresses vacation auto-responder loops.
4. **`Precedence: bulk`**: RFC compliance for automated transactional dispatches.
5. **`List-Unsubscribe` & `List-Unsubscribe-Post`**: One-click unsubscribe header mandated by Google & Yahoo since February 2024.
6. **`Return-Path`**: Designated bounces address (`bounces@domain`).

---

## 3. iCalendar (.ics) RFC 5545 Interactivity

To enable **Gmail and Outlook one-click RSVP widgets** directly inside the inbox message card:

1. **MIME Structure**:
   ```text
   multipart/mixed
   ├── multipart/alternative
   │   ├── text/plain
   │   ├── text/html
   │   └── text/calendar; method=REQUEST; charset=UTF-8
   └── text/calendar; name="invite.ics" (attachment)
   ```
2. **Outlook Content-Class**: `urn:content-classes:calendarmessage` triggers Outlook's native calendar parsing.
3. **METHOD=REQUEST**: Instructs Google Calendar to automatically stage the event on the candidate's agenda with `RSVP: Needs Action`.

---

## 4. Anti-SPAM Copywriting Rules (CAN-SPAM Act)

Heketon enforces compliance with international anti-spam regulations:
- **Physical Address**: Verified physical headquarters address in email footer (`Menara BTPN Lt. 32, Jakarta Selatan`).
- **Clear Identification**: Explicit identification of the sender and interview context in the header.
- **No Deceptive Subjects**: Clean, professional Indonesian & English subjects without deceptive clickbait or all-caps shouting.
- **Balanced Text-to-HTML Ratio**: Clean inline styles, no external JavaScript or iframe tags, no suspicious short links.
