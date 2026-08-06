# Shopify policy text

The four policies at `/policies/*` are **not** theme pages. Their text lives in
Shopify admin under **Settings → Policies**, and the theme renders it through
`templates/policy.json` and `sections/main-policy.liquid` — which is what gives
them the site's design. Before that template existed they rendered unstyled, and
were the only pages on the site that looked like a different shop.

## Why these are files rather than already applied

The Shopify connector this theme is managed through does not hold the
`write_legal_policies` scope, so the policies cannot be written by API. Verified
again on 2026-08-06: `shopPolicyUpdate` returns *"Access denied … Required
access: write_legal_policies"*. They have to be pasted in once by hand:

**Shopify admin → Settings → Policies →** pick the policy → paste → Save.

Shopify renders these with Liquid, which is why the text uses `{{ shop_name }}`,
`{{ email }}`, `{{ phone }}` and `{{ address }}` — the same variables Shopify's
own default policies use. They resolve from Settings → Store details, so the
address and phone number stay correct in one place.

Current state on the store: privacy is still unedited Shopify boilerplate
(American spellings, "powered by Shopify"); the other three are empty.

## Before pasting: one setting must change

`shipping-policy.html` and the buy widget both state **free UK delivery on two
pairs or more**. Shopify's actual rule is `TOTAL_PRICE >= £50`, and two pairs is
£36.99 after the automatic discount — so a customer promised free delivery is
charged £4.99 at checkout. Free delivery currently starts at three pairs.

**Fix in Settings → Shipping and delivery → General profile → United Kingdom →
edit the free "Standard" rate → change the condition from £50 to £35.** It could
not be done by API: that rate uses a newer condition type and
`deliveryProfileUpdate` refuses it with *"uses new configurations that are only
available through Shopify's updated APIs"*.

The theme's own `free_delivery_threshold` is already set to 35 to match.

## What this text is, and is not

Drafts written to UK consumer and data protection law as at August 2026, in the
site's voice. Not legal advice, and the terms and privacy policy in particular
should be read by a solicitor before publication.

Where it states a period — 14 days to cancel, a further 14 to return, 30 days to
reject faulty goods, six months of reversed burden — that is UK statute, not a
figure anyone invented: the Consumer Contracts (Information, Cancellation and
Additional Charges) Regulations 2013 and the Consumer Rights Act 2015.

Two instruments changed recently enough that most templates in circulation are
out of date, and both are handled here:

- The **Consumer Protection from Unfair Trading Regulations 2008** were replaced
  in full by the **Digital Markets, Competition and Consumers Act 2024** on
  6 April 2025. Nothing here cites the 2008 regulations.
- The **EU Online Dispute Resolution platform** was switched off on 20 July 2025.
  No ODR link appears in any of these files. Shopify defaults frequently still
  carry one — check nothing reintroduces it.

## Decisions already taken

- **Return postage** — HydroSox pays the first return per customer; faulty goods
  are always free to return. Stated in `refund-policy.html`. Under the CCR 2013
  this must also appear in pre-contract information at checkout, or the trader
  pays by default.
- **Warranty** — twelve months against manufacturing defects, on top of
  statutory rights. Lives on `/pages/warranty`, not in these files.
- **Single-pair delivery** — £4.99, shown as a total in the buy widget, which is
  what the DMCCA 2024 requires.
- **International** — EU £14.99, rest of world £23.99. Read from the store's own
  delivery profile, so it is real rather than assumed.

## Still outstanding

Search for **[CONFIRM]** before pasting. It covers:

- dispatch cut-off, carrier and transit time, and whether tracking is sent
  (`shipping-policy.html`)
- the returns address (`refund-policy.html`)
- the Companies House registration number (`terms-of-service.html`,
  `privacy-policy.html`) — required by the Companies Act 2006 and the
  E-Commerce Regulations 2002, and currently absent from the whole site
- the named list of data processors (`privacy-policy.html`) — UK GDPR expects
  specificity, and categories alone are weak
