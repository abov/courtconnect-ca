# Email provider comparison (ADR 0025, option B)

Draft 2026-11-11. Not a decision: the owner picks the provider, sender and privacy text after the beta (beta question 10). Figures come from each provider's public pricing page on 2026-11-11 and change often; recheck before signing up. "?" means the page did not say or the fetch failed, so verify it by hand.

## What we need (from ADR 0025)
- Free or near-free at a few hundred to a few thousand subscribers; 2 sends a month.
- Double opt-in, one-click unsubscribe, and a hosted form the static page can post to (no backend of ours).
- Per-subscriber tags or fields (venue ids, home place, sports) so the provider merges the digest at send time; the agent never reads the list.
- Sender is the project contact, never the owner's personal email. A free-mail sender (gmail.com) usually fails DMARC, so plan on a project domain or the provider's shared one.
- A postal address in the footer (CAN-SPAM). Decide which address before launch.

## Comparison
| Provider (free tier) | Subscribers | Sends | Tags / segments | Double opt-in | API on free | Branding on free | Notes |
|---|---|---|---|---|---|---|---|
| Kit | up to 10,000 | no limit stated | tags + segments included | ? | yes (listed) | yes | Biggest free list; removing branding is $33/mo |
| MailerLite | 250 | 2,500/month | groups + segments unlimited | ? | limited, no sending | yes | 3 forms; sending locks above 250 |
| Buttondown | 100 | 1 email/day to full list | tags are a +$9/mo add-on | ? | ? | ? | Custom sender domain included; small list only |
| Mailchimp | 250 | 500/month, 250/day | ? | ? | ? | yes | 250 subscribers x 2 sends = 500, so the cap is hit at once |
| Brevo | page gave no figures (from memory ~300 emails/day, unlimited contacts; unverified) | ? | ? | ? | ? | yes | Page names confirmation signups and forms; recheck numbers |

## Read
- **Kit** fits best on paper: a free list large enough for the beta and beyond, tags, API. Open items are double opt-in on the free plan, the footer branding, and how many tags one subscriber can carry (a person may save up to 30 venues, so venue ids as tags could be heavy; custom fields or a per-region tag may work instead).
- **MailerLite** is the fallback: 250 subscribers and 2,500 sends cover twice-monthly mail to a small list, but sending stops at 250 and its free API cannot send.
- **Buttondown** is good for a plain newsletter but tags cost extra and the free list is 100.
- **Mailchimp** is the weakest fit (500 sends a month, one audience).
- Anything beyond ~10,000 subscribers is a paid tier everywhere; that is a monetization question (`docs/monetization_ideas.md`), not a beta one.

## To check before choosing
1. Double opt-in on the free plan, and whether unconfirmed addresses expire (ADR says 7 days).
2. Can the digest be created as a draft by API or CSV so the owner approves each send (ADR draft mode)?
3. Sender setup: project domain needed? Reply-to as the project contact?
4. Footer: can the postal address be a PO box or a registered-agent address?
5. Privacy: processor location, delete-my-data handling, export on leaving.
6. Tag or field limits per subscriber, and whether the hosted form can set tags from a URL or hidden fields (favorites pre-filled from `cc.shortlist`).

## Not covered
Resend/Postmark/SES (need our own backend, so option C in ADR 0025, rejected) and Substack/Beehiiv (publication-first, weak per-subscriber tags).
