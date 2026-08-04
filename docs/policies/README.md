# Default policy text

Three of the four Shopify policies had no text, so the footer was publishing
links to `/policies/terms-of-service`, `/policies/refund-policy` and
`/policies/shipping-policy` that all returned 404. Those were the pages that
were not coming up.

The theme no longer links to a policy that has no text — see the `legal_link`
block in `sections/footer.liquid` — so nothing is broken while these are
outstanding. Each link reappears by itself once its policy is written.

## Why these are files rather than already applied

The Shopify connector this theme is managed through does not hold the
`write_legal_policies` scope, so the policies cannot be written by API. They
have to be pasted in once by hand:

**Shopify admin → Settings → Policies →** pick the policy → paste → Save.

Shopify renders these with Liquid, which is why the text uses `{{ shop_name }}`,
`{{ email }}`, `{{ phone }}` and `{{ address }}` — the same variables Shopify's
own default privacy policy uses. They resolve from Settings → Store details, so
the address and phone number stay correct in one place.

## What this text is, and is not

It is default text, in the site's voice, so the pages are not missing. It is
not a substitute for advice.

Where it states a period — 14 days to cancel, a further 14 days to return, 30
days to reject faulty goods — that is UK statute, not a figure anyone invented:
the Consumer Contracts (Information, Cancellation and Additional Charges)
Regulations 2013 and the Consumer Rights Act 2015.

Everywhere a real commercial decision is needed it says **[CONFIRM]** instead
of guessing. Search for that word before launch. It covers:

- who pays return postage, and the return address
- any warranty beyond statutory rights
- dispatch cut-off and carrier transit times
- whether tracking is provided
- destinations shipped to, and duties outside the UK
- whether a second delivery attempt is charged
- registered company number and VAT number

The delivery threshold is the one commercial fact already stated, because it is
already live on the site: free delivery on two pairs or more.
