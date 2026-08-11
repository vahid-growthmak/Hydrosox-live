# Shopify policies — paste-ready

Everything in this file goes into **Shopify admin → Settings → Policies**. Paste
one policy at a time, save, and check the page before moving to the next.

The text below is the Phase 6 document's content and nothing else. Where that
document said `[TO CONFIRM]`, the marker is still there — search for it before
you save, and either fill it in or delete the sentence. Nothing has been
invented to fill a gap.

---

## Before you paste anything: two things

### 1. Turn OFF "Automated" on the Privacy policy

Your Policies screen shows **Privacy policy — Automated**. That is Shopify
generating its own text, which is why that page is a wall of American-English
boilerplate that says "powered by Shopify" and "Personalize". No amount of
theme design changes it, because the words are not yours.

Open **Privacy policy**, switch off the automated/"Use Shopify's template"
option, clear the field, then paste the version below.

### 2. Paste as HTML, not as rich text

Each block below is HTML. In the policy editor, click the **`<>`** (Show HTML)
button in the toolbar, delete anything already in the box, and paste. Pasting
into the rich-text view instead will keep the tags as visible text.

The theme already styles whatever arrives — `templates/policy.liquid` and
`sections/main-policy.liquid` put policy pages on the same type scale, measure
and rules as the Cookie Policy and Accessibility pages. That went live at
14:09 on 6 August 2026, so if you looked before then you saw the unstyled
version.

### 3. The contact details below are written out, not templated

An earlier version of this file used Liquid tags here — `shop_name`, `phone`,
`email`, `address` in double braces — on the assumption that Shopify would
resolve them from **Settings → Store details**.

**It does not.** A policy body is stored as plain HTML and is never parsed as
Liquid. The theme renders it with `policy.body`, and Liquid prints a variable's
value; it does not re-parse what is inside it. Shopify's own checkout policy
modals do not parse it either.

The result was that customers saw the literal braces on
/policies/refund-policy and, worse, inside the Contact modal at checkout.

So every value below is written out in full. The cost is that changing the
phone number means editing these six policies as well as Settings; that is the
price of it being right on screen. The values as at 11 August 2026:

| Tag that used to be here | Value now written out |
| --- | --- |
| shop_name | HydroSox |
| phone | 0203 4322 920 *(calls only)* |
| email | info@hydrosox.com |
| address | 399-405 Oxford Street, Mayfair, London, W1C 2BU, United Kingdom |

WhatsApp (+44 7441 396244) is now given alongside the phone number wherever a
policy offers a way to reach a person, per the client's rule that the calls
number and the WhatsApp number always appear together.

---

## 1. Shipping policy

**Settings → Policies → Shipping policy**

```html
<p>Everything below is either already true at checkout or openly unfinished. Nothing in between.</p>

<h2>Settled today</h2>

<p><strong>Free on two pairs or more.</strong> The threshold sits at the two-pair price, so the saving and the free delivery arrive together. Buying a second pair costs £16.99 and removes the delivery charge.</p>

<p><strong>On a single pair, delivery is charged.</strong> The exact amount is shown with the price before you add anything to the basket, not revealed at checkout. You are never charged a delivery cost you have not already seen.</p>

<p><strong>Dispatched from the United Kingdom.</strong> HydroSox is a UK company holding UK stock. Nothing is drop-shipped from elsewhere, and nothing arrives with an unexpected customs charge.</p>

<p><strong>No delivery speed is promised.</strong> We will not print a next-day promise that confirmed stock cannot support, so no delivery speed appears anywhere on this site until it can. When a service level is confirmed it will be stated here in full.</p>

<p><strong>Risk passes on delivery.</strong> Until the parcel is delivered to the address you gave at checkout, responsibility for it is ours. If it does not arrive, contact us and we will resolve it with the carrier.</p>

<h2>Still being confirmed</h2>

<p><strong>Dispatch cut-off.</strong> [TO CONFIRM — the time of day after which an order ships the next working day.]</p>

<p><strong>Carrier and transit time.</strong> [TO CONFIRM — who carries it, and the expected number of working days.]</p>

<p><strong>Tracking.</strong> [TO CONFIRM — whether a tracking link is sent, and by whom.]</p>

<p><strong>Outside the UK.</strong> [TO CONFIRM — whether international orders are accepted, and how duties are handled.]</p>

<h2>Questions</h2>

<p>Phone 0203 4322 920 during the day, message us on WhatsApp at +44 7441 396244, or email info@hydrosox.com at any time. Both are published on every page of this site rather than held behind a form.</p>
```

---

## 2. Return and refund policy

**Settings → Policies → Return and refund policy**

```html
<p>Your statutory rights are the floor here, not the ceiling. Nothing on this page reduces them.</p>

<h2>Changing your mind</h2>

<p><strong>Tell us within 14 days.</strong> Fourteen days from the day the parcel arrives. Email or phone us — a clear statement that you are cancelling is enough, and there is no form to find. If you would rather use one, the model cancellation form set out in the Consumer Contracts Regulations 2013 is accepted.</p>

<p><strong>Send them back within 14 more.</strong> Unworn, in the original packaging, with any seal intact. You may inspect them as you would in a shop — trying a pair on briefly to check the size is inspection, not use.</p>

<p><strong>Checked on arrival.</strong> Every pair that comes back is inspected by our safety and compliance team. They make the final decision on whether a return is viable for a refund.</p>

<p><strong>Refunded to the card you paid with.</strong> Where a refund is accepted we return the price of the socks. It can take up to 30 days from our side for the funds to reach your account.</p>

<p><strong>Who pays to send them back.</strong> We do, on your first return. After that, return postage is yours to cover unless the goods are faulty — in which case we pay, every time.</p>

<p><strong>Where to send them.</strong> [TO CONFIRM — the returns address. The registered office at 399–405 Oxford Street may not be the correct destination for parcels.]</p>

<h2>If something is actually wrong with them</h2>

<p><strong>Within 30 days, reject and get a full refund.</strong> Under the Consumer Rights Act 2015 goods must be of satisfactory quality, fit for purpose and as described. Within thirty days of delivery you have a short-term right to reject faulty goods and receive a full refund. No repair attempt is required first.</p>

<p><strong>After 30 days, repair or replacement.</strong> And a refund or price reduction if that does not resolve it. We do not charge for returning faulty goods, at any point.</p>

<p><strong>Within six months, the fault is presumed ours.</strong> If a fault appears within six months of delivery it is assumed to have been present from the start, unless we can show otherwise. After six months the burden shifts, but the goods must still last a reasonable time.</p>

<p><strong>This sits on top of your statutory rights.</strong> Nothing in this policy replaces or reduces your rights under the Consumer Rights Act 2015 or the Consumer Contracts Regulations 2013. Where this policy is more generous than the law, the more generous term applies.</p>

<h2>What is not covered</h2>

<p><strong>Normal wear is not a fault.</strong> A membrane ends through abrasion, heat and clogged pores. That is wear, not a defect. The returns page draws the line between the two in detail.</p>

<p><strong>Damage from misuse or incorrect care.</strong> Tumble drying, ironing, direct heat, bleach and fabric softener will all shorten or end the life of a membrane. Care instructions are published in full and linked from the product page.</p>

<p><strong>Worn socks returned as change-of-mind.</strong> Hygiene. A pair that has been worn cannot be resold, and cannot be returned simply because you changed your mind. A faulty pair is a different matter and worn or not makes no difference to it.</p>

<h2>How to start a return</h2>

<p>Email info@hydrosox.com, phone 0203 4322 920, or message us on WhatsApp at +44 7441 396244 with your order number. Contact us before sending anything back and we will tell you exactly what to do.</p>
```

---

## 3. Terms of service

**Settings → Policies → Terms of service**

```html
<p>These govern your use of this website and anything you buy from us. Nothing in them reduces your statutory rights as a consumer.</p>

<h2>1. Who we are</h2>
<p>This website is operated by Hydrosox Ltd, a company registered in England and Wales under company number [TO CONFIRM], with its registered office at 399-405 Oxford Street, Mayfair, London, W1C 2BU, United Kingdom. You can contact us at info@hydrosox.com, on 0203 4322 920, or on WhatsApp at +44 7441 396244.</p>

<h2>2. Using this website</h2>
<p>By using this site you confirm you are at least 18, or have the consent of a parent or guardian.</p>
<p>You agree to use it lawfully, and not in a way that restricts anyone else's use of it. You must not attempt to gain unauthorised access, introduce malicious software, or disrupt the site or its services.</p>
<p>We may restrict or end access if we reasonably suspect misuse.</p>

<h2>3. Product information</h2>
<p>We take reasonable care to make sure descriptions, images, specifications and prices are accurate and current.</p>
<p>Minor variation in colour, texture or appearance can occur through manufacturing and through differences in screen settings. That is not a defect.</p>
<p>Where we discover an error in a description or a price, we will tell you before dispatch and you may cancel.</p>

<h2>4. Orders and when a contract is formed</h2>
<p>Placing an order is an offer to buy, subject to these terms. All orders are subject to acceptance and availability.</p>
<p>A contract is formed when we confirm dispatch of your order, not when you place it.</p>
<p>We may refuse or cancel an order before dispatch — for suspected fraud, a pricing or technical error, a stock problem, or a breach of these terms. If payment has been taken, you receive a full refund to the original payment method.</p>

<h2>5. Prices and payment</h2>
<p>All prices are in pounds sterling and include VAT.</p>
<p>The price shown when you place your order is the price you pay. We may change prices at any time, but a change never affects an order already confirmed.</p>
<p>Where a delivery charge applies, the total price including it is shown before you commit to buying.</p>
<p>Payment is taken in full at the time of purchase, through secure third-party processors. We do not store full card details.</p>

<h2>6. Delivery and risk</h2>
<p>Delivery timescales are estimates unless we state otherwise.</p>
<p>We are not responsible for delays caused by carriers, customs, weather, industrial action or other circumstances outside our reasonable control — but if a parcel is delayed or lost after dispatch we will work with the carrier to resolve it.</p>
<p>Risk in the goods passes to you when they are delivered to the address you gave at checkout.</p>

<h2>7. Cancellation, returns and refunds</h2>
<p>Your right to cancel a distance sale within 14 days, and your rights if goods are faulty, are set out in full on our returns page, which forms part of these terms.</p>
<p>Nothing in these terms limits your rights under the Consumer Rights Act 2015 or the Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013.</p>

<h2>8. Our liability to you</h2>
<p>We do not exclude or limit our liability for death or personal injury caused by our negligence, for fraud or fraudulent misrepresentation, or for anything else that cannot lawfully be excluded.</p>
<p>Subject to that, our liability for any claim arising from an order is limited to the price you paid for the goods.</p>
<p>We are not liable for losses that were not reasonably foreseeable when the contract was made.</p>

<h2>9. Intellectual property</h2>
<p>The content of this site — text, images, video, design and trade marks — belongs to us or is used under licence. You may not reproduce it commercially without our written permission.</p>
<p>Porelle&reg; is a trade mark of its owner and is used here under licence.</p>

<h2>10. Things outside our control</h2>
<p>We are not liable for failure or delay caused by events outside our reasonable control, including natural events, war, industrial action, supply chain disruption or governmental action.</p>

<h2>11. General</h2>
<p>If any provision of these terms is found to be invalid, the rest remain in force.</p>
<p>These terms, together with our privacy policy, cookie policy, returns policy and delivery policy, form the whole agreement between us.</p>
<p>We may update these terms. The version that applies to your order is the one published when you placed it.</p>

<h2>12. Complaints</h2>
<p>If something has gone wrong, email info@hydrosox.com or phone 0203 4322 920 and we will try to resolve it directly.</p>
<p>We are not currently a member of an alternative dispute resolution scheme. If we cannot resolve a complaint between us, you retain your right to bring a claim in the courts.</p>

<h2>13. Governing law</h2>
<p>These terms are governed by the laws of England and Wales, and disputes are subject to the exclusive jurisdiction of the courts of England and Wales. If you live in Scotland or Northern Ireland, you may also bring proceedings in the courts there.</p>
```

---

## 4. Privacy policy

**Settings → Policies → Privacy policy** — turn off "Automated" first.

```html
<p>Hydrosox Ltd is the data controller for everything described here. If any of it is unclear, email us and a person will explain it — that is a faster route than reading it twice.</p>

<h2>Who we are</h2>

<p><strong>The controller.</strong> Hydrosox Ltd, a company registered in England and Wales [company number to be inserted], of 399-405 Oxford Street, Mayfair, London, W1C 2BU, United Kingdom, is the data controller for personal data processed through this website.</p>

<p><strong>How to reach us about data.</strong> Email info@hydrosox.com or phone 0203 4322 920. We do not currently have a Data Protection Officer, and are not required to appoint one.</p>

<h2>What we collect</h2>

<p><strong>Information you give us.</strong> Your name, email address, telephone number, and billing and delivery addresses when you place an order. Anything you write to us when you get in touch. Your email address if you subscribe to the newsletter.</p>

<p><strong>Information about your order.</strong> What you bought, when, at what price, and its delivery status.</p>

<p><strong>Payment information.</strong> Handled entirely by our payment providers. We do not see, hold or store full card details at any point.</p>

<p><strong>Technical information collected automatically.</strong> IP address, device and browser type, operating system, referring source, pages viewed, time on page, and how you interacted with the site. Collected through cookies and similar technologies — see the cookie policy.</p>

<p><strong>Information from third parties.</strong> Our payment processors, delivery partners, analytics providers and advertising platforms may pass us information relating to your order or your visit.</p>

<h2>Why we use it, and our lawful basis</h2>

<p>UK GDPR requires a lawful basis for each purpose. Ours are:</p>

<ul>
  <li><strong>Taking and fulfilling your order, arranging delivery, handling returns and refunds</strong> — performance of a contract.</li>
  <li><strong>Answering questions and providing customer support</strong> — performance of a contract, or our legitimate interest in running the business properly.</li>
  <li><strong>Keeping records for tax and accounting</strong> — legal obligation.</li>
  <li><strong>Preventing fraud and keeping the site secure</strong> — legitimate interest in protecting the business and its customers.</li>
  <li><strong>Understanding how the site is used and improving it</strong> — legitimate interest, and consent where non-essential cookies are involved.</li>
  <li><strong>Sending marketing emails</strong> — consent. You can withdraw it at any time and every email carries an unsubscribe link.</li>
  <li><strong>Advertising, including audiences built from site activity</strong> — consent, given through the cookie banner.</li>
</ul>

<h2>Who we share it with</h2>

<p><strong>We do not sell your data.</strong> Not to anyone, in any circumstances.</p>

<p><strong>Service providers who need it to do their job.</strong> Payment processors, delivery companies, our ecommerce platform and hosting provider, email and analytics providers, and fraud prevention services. [TO CONFIRM — name each provider here. UK GDPR expects specificity, and a named list is materially more defensible than a list of categories.] Each is bound by contract to process personal data only on our instructions and to keep it secure.</p>

<p><strong>Where the law requires it.</strong> Where we are obliged to disclose by law, regulation, court order or a competent authority, or where disclosure is necessary to prevent fraud or to protect our legal rights.</p>

<h2>Sending data outside the UK</h2>

<p><strong>Some of our providers are outside the UK.</strong> Where personal data is transferred outside the United Kingdom, we rely on UK adequacy regulations where they apply, or on the International Data Transfer Agreement or the UK Addendum to the EU standard contractual clauses where they do not.</p>

<h2>How long we keep it</h2>

<ul>
  <li><strong>Order and transaction records</strong> — six years from the end of the financial year in which the order was placed, to meet HMRC record-keeping requirements.</li>
  <li><strong>Customer service correspondence</strong> — [TO CONFIRM — two years is a common and defensible period.]</li>
  <li><strong>Marketing consent and email address</strong> — until you unsubscribe, plus a short suppression record thereafter, so we do not email you again after you have asked us not to.</li>
  <li><strong>Analytics and website usage data</strong> — [TO CONFIRM — set in the analytics platform, commonly 14 months.]</li>
</ul>

<h2>Your rights</h2>

<p><strong>What you can ask for.</strong> Access to the data we hold about you; correction of anything inaccurate; erasure; restriction of processing; objection to processing carried out on the basis of legitimate interests; portability of data you gave us; and withdrawal of consent at any time where processing relies on it.</p>

<p><strong>How to exercise them.</strong> Email info@hydrosox.com. We will respond within one month. We may ask you to confirm your identity first, which is a protection for you rather than an obstacle.</p>

<p><strong>It is free.</strong> There is no charge for making a request, unless a request is manifestly unfounded or excessive.</p>

<p><strong>If you are not satisfied.</strong> You can complain to the Information Commissioner's Office at ico.org.uk, or by calling 0303 123 1113. We would rather you came to us first so we can put it right, but you do not have to.</p>

<h2>Security, children and other sites</h2>

<p><strong>Security.</strong> We use appropriate technical and organisational measures to protect personal data. No transmission over the internet is completely secure, and we cannot guarantee absolute security — but we take it seriously and we would tell you promptly if something went wrong.</p>

<p><strong>Children.</strong> This site is not intended for children under 16 and we do not knowingly collect their data. If we become aware that we have, we will delete it.</p>

<p><strong>Other websites.</strong> Links to other sites are not our responsibility. Their privacy practices are their own and we would encourage you to read them.</p>

<p><strong>Changes to this policy.</strong> If we change it, the revised version appears here with a new date. Where a change is significant we will tell you rather than relying on you to notice.</p>
```

---

## 5. Contact information

**Settings → Policies → Contact information** — Shopify marks this **Required**.

The Phase 6 document does not cover this slot. It is not a policy so much as the
trader-identity information the E-Commerce Regulations 2002 and the Companies
Act 2006 require, which the document does call for. Built only from company
details already published on the site:

```html
<p>HydroSox is operated by Hydrosox Ltd, a company registered in England and Wales under company number [TO CONFIRM].</p>

<p><strong>Registered address.</strong> 399-405 Oxford Street, Mayfair, London, W1C 2BU, United Kingdom</p>

<p><strong>Phone.</strong> 0203 4322 920</p>

<p><strong>WhatsApp.</strong> +44 7441 396244</p>

<p><strong>Email.</strong> info@hydrosox.com</p>

<p>Both the phone number and the email address are published on every page of this site rather than held behind a contact form.</p>
```

---

## 6. Legal notice

**Settings → Policies → Legal notice**

The Phase 6 document does not cover this slot either, and it is optional in the
UK — it is mainly used for the German *Impressum*. **Leave it empty** unless a
solicitor says otherwise. An empty slot is better than a duplicate of the
contact information.

---

## After pasting

**Check the footer.** The theme hides a legal link whose policy has no text, so
each link reappears by itself once its policy is saved. Shipping, Returns and
Terms should all appear in the footer once you have pasted them.

**Check one page.** Open `/policies/privacy-policy`. It should now carry the
site's header, breadcrumb, type scale and footer, exactly like the Cookie Policy
and Accessibility pages, with your text in place of Shopify's.

---

## Still outstanding

Search every block above for **`[TO CONFIRM]`** before saving. Between them they
cover:

| Missing fact | Blocks |
| --- | --- |
| Dispatch cut-off, carrier, transit time, tracking | Shipping |
| Whether international orders are accepted, and how duties are handled | Shipping |
| The returns address | Returns |
| Companies House registration number | Terms, Privacy, Contact information |
| Named list of data processors | Privacy |
| Customer service and analytics retention periods | Privacy |

Two of these are not policy problems and cannot be fixed by pasting text:

- **The free-delivery threshold.** The site promises free UK delivery on two
  pairs. Shopify's rule is `TOTAL_PRICE >= £50`, and two pairs is £36.99 after
  the automatic discount — so that promise is currently broken at checkout. Fix
  in **Settings → Shipping and delivery → General profile → United Kingdom →
  edit the free "Standard" rate → change £50 to £35.** The theme already reads
  £35.
- **The cookie consent banner.** The Cookie Policy describes a consent standard
  the site does not yet meet. No non-essential tag may fire before consent,
  "Reject all" must be as prominent as "Accept all", and the cookie table cannot
  be written until the tags exist.

---

## A reminder about what this is

These are drafts written to UK consumer and data protection law as at August
2026, in the site's voice. Growthmak is not a firm of solicitors and this is not
legal advice. The Terms and the Privacy Policy in particular should be read by
one before they go live.
