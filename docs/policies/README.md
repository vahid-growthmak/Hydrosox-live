# Shopify policy text

**The paste-ready content is in [SHOPIFY-POLICIES.md](SHOPIFY-POLICIES.md).**
One file, one HTML block per Shopify policy slot, ready to paste by hand.

It replaced four separate `.html` files so there is a single source — that
content has been through several revisions and two copies would drift.

## Why it is pasted rather than pushed

The four policies at `/policies/*` are **not** theme pages. Their text lives in
Shopify admin under **Settings → Policies**, and the connector this theme is
managed through does not hold the `write_legal_policies` scope, so they cannot
be written by API. Verified 2026-08-06: `shopPolicyUpdate` returns *"Access
denied … Required access: write_legal_policies"*.

The theme renders them through `templates/policy.liquid` and
`sections/main-policy.liquid`, which is what puts them on the site's own type
scale and rules. Before that template existed they rendered unstyled, and were
the only pages on the site that looked like a different shop.

## The privacy policy is a special case

It is set to **Automated** in the admin — Shopify generating its own text. That
is why it reads as American-English boilerplate that says "powered by Shopify".
Theme design cannot change it, because the words are not ours. The automated
option has to be switched off before the replacement is pasted.

## One setting that is not a policy

`shipping-policy.html` promised free UK delivery on two pairs while Shopify's
rule is `TOTAL_PRICE >= £50`; two pairs is £36.99 after the automatic discount,
so the promise breaks at checkout. Fix in **Settings → Shipping and delivery →
General profile → United Kingdom → edit the free "Standard" rate → £50 to £35.**
It could not be done by API — that rate uses a newer condition type and
`deliveryProfileUpdate` refuses it. The theme's own `free_delivery_threshold` is
already 35.

## What this text is, and is not

Drafts written to UK consumer and data protection law as at August 2026, in the
site's voice. Not legal advice; the terms and privacy policy in particular
should be read by a solicitor before publication.

Where it states a period — 14 days to cancel, a further 14 to return, 30 days to
reject faulty goods, six months of reversed burden — that is UK statute, not a
figure anyone invented.

Two instruments changed recently enough that most templates in circulation are
out of date, and both are handled:

- The **Consumer Protection from Unfair Trading Regulations 2008** were replaced
  in full by the **DMCCA 2024** on 6 April 2025. Nothing cites the 2008 rules.
- The **EU Online Dispute Resolution platform** was switched off on 20 July 2025.
  No ODR link appears anywhere. Shopify defaults frequently still carry one —
  check nothing reintroduces it.
