#!/usr/bin/env python3
"""Builds /pages/privacy-policy and /pages/terms-of-service as theme pages.

Shopify's own policies at /policies/* are one blob of merchant HTML rendered
through a single section. However well that section is styled it can only ever
be a styled blob — it has no eyebrows, no section rhythm, no sticky headings,
because there are no sections in it to give those to. Beside the cookie policy,
which is a real theme page, it looks like a different site.

Shipping and returns were already solved this way: /pages/shipping-and-delivery
and /pages/returns-and-refunds are theme pages, and the Shopify policy is
referenced as "the formal version". Privacy and terms were the two with no theme
page at all, which is why they are the two that look wrong.

So they get the same treatment and the same shape as the cookie policy:
breadcrumb, a centred opening, clause groups as content-columns, a centred
close. The Shopify policies stay — checkout links to them and they are the
binding text — but the designed page is what the footer points at and what
search indexes. See the noindex rule in layout/theme.liquid.

Nine clause groups in a row would rebuild exactly the wall this theme has been
fixing everywhere else, so the rhythm rule applies here too: no two adjacent
sections share more than one of layout, background and heading side.

No [TO CONFIRM] marker reaches a template. The company registration number is
not written into the copy at all — it lives in a theme setting and the footer
renders it site-wide the moment it is filled in.

Idempotent.
"""
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates"


def rich(*paras):
    return "".join("<p>%s</p>" % p.strip() for p in paras if p and p.strip())


def crumb(label):
    return collections.OrderedDict([
        ("type", "breadcrumb"),
        ("settings", collections.OrderedDict([
            ("color_scheme", "paper"), ("home_label", "Home"),
            ("current_label", label)])),
    ])


def note(anchor, eyebrow, heading, body, scheme="paper", footnote=None,
         cta=None, link=None, heading_tag=None):
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("anchor_id", anchor),
        ("eyebrow", eyebrow), ("heading", heading), ("body", rich(*body))])
    if heading_tag:
        st["heading_tag"] = heading_tag
    if footnote:
        st["footnote"] = rich(footnote)
    if cta:
        st["cta_label"], st["cta_url"] = cta
    if link:
        st["link_label"], st["link_url"] = link
    return collections.OrderedDict([("type", "centre-note"), ("settings", st)])


def cols(anchor, eyebrow, heading, lede, entries,
         layout="list", scheme="paper", mirror=False, link=None):
    blocks, order = collections.OrderedDict(), []
    for n, (title, body) in enumerate(entries, 1):
        k = "i%d" % n
        blocks[k] = collections.OrderedDict([
            ("type", "item"),
            ("settings", collections.OrderedDict([
                ("title", title), ("body", rich(body))]))])
        order.append(k)
    st = collections.OrderedDict([
        ("color_scheme", scheme), ("layout", layout), ("numbered", False),
        ("mirror", mirror), ("anchor_id", anchor),
        ("eyebrow", eyebrow), ("heading", heading)])
    if lede:
        st["lede"] = rich(lede)
    if link:
        st["link_label"], st["link_url"] = link
    return collections.OrderedDict([
        ("type", "content-columns"), ("settings", st),
        ("blocks", blocks), ("block_order", order)])


def write(handle, sections, order, what):
    header = ("/* %s, composed by scripts/build-legal-pages.py.\n"
              "   Re-run that script rather than hand-editing; the section content\n"
              "   itself stays editable in the Shopify theme editor. */\n" % what)
    data = collections.OrderedDict([("sections", sections), ("order", order)])
    (TPL / ("page.%s.json" % handle)).write_text(
        header + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print("  %-22s %d sections" % (handle, len(order)))


# ===========================================================================
def privacy():
    S = collections.OrderedDict()
    S["crumb"] = crumb("Privacy policy")

    S["intro"] = note(
        "privacy", "Privacy policy",
        "What we do with your data.",
        ["Hydrosox Ltd is the data controller for everything described here. "
         "If any of it is unclear, email us and a person will explain it — that "
         "is a faster route than reading it twice."],
        heading_tag="h1")

    S["who"] = cols(
        "who-we-are", "Who we are", "Who we are.", None,
        [("The controller",
          "Hydrosox Ltd, a company registered in England and Wales, of "
          "399–405 Oxford Street, Mayfair, London W1C 2BU, is the data "
          "controller for personal data processed through this website."),
         ("How to reach us about data",
          "Email info@hydrosox.com or phone 0203 4322 920. We do not currently "
          "have a Data Protection Officer, and are not required to appoint "
          "one.")],
        layout="split")

    S["collect"] = cols(
        "what-we-collect", "What we collect", "What we collect.",
        "Five kinds of thing, and no more than that.",
        [("Information you give us",
          "Your name, email address, telephone number, and billing and "
          "delivery addresses when you place an order. Anything you write to "
          "us when you get in touch. Your email address if you subscribe to "
          "the newsletter."),
         ("Information about your order",
          "What you bought, when, at what price, and its delivery status."),
         ("Payment information",
          "Handled entirely by our payment providers. We do not see, hold or "
          "store full card details at any point."),
         ("Technical information collected automatically",
          "IP address, device and browser type, operating system, referring "
          "source, pages viewed, time on page, and how you interacted with the "
          "site. Collected through cookies and similar technologies."),
         ("Information from third parties",
          "Our payment processors, delivery partners, analytics providers and "
          "advertising platforms may pass us information relating to your "
          "order or your visit.")],
        layout="steps", link=("What the cookies do", "/pages/cookie-policy"))

    S["basis"] = cols(
        "lawful-basis", "Lawful basis", "Why we use it, and on what basis.",
        "UK GDPR requires a lawful basis for each purpose. These are ours.",
        [("Taking and fulfilling your order",
          "Arranging delivery, handling returns and refunds — performance of a "
          "contract."),
         ("Answering questions and providing support",
          "Performance of a contract, or our legitimate interest in running "
          "the business properly."),
         ("Keeping records for tax and accounting",
          "A legal obligation."),
         ("Preventing fraud and keeping the site secure",
          "Our legitimate interest in protecting the business and its "
          "customers."),
         ("Understanding how the site is used and improving it",
          "Legitimate interest, and consent where non-essential cookies are "
          "involved."),
         ("Sending marketing emails",
          "Consent. You can withdraw it at any time and every email carries an "
          "unsubscribe link."),
         ("Advertising, including audiences built from site activity",
          "Consent, given through the cookie banner.")],
        layout="focus", scheme="ink", mirror=True)

    S["share"] = cols(
        "who-we-share-with", "Sharing", "Who we share it with.", None,
        [("We do not sell your data",
          "Not to anyone, in any circumstances."),
         ("Service providers who need it to do their job",
          "Payment processors, delivery companies, our ecommerce platform and "
          "hosting provider, email and analytics providers, and fraud "
          "prevention services. Each is bound by contract to process personal "
          "data only on our instructions and to keep it secure."),
         ("Where the law requires it",
          "Where we are obliged to disclose by law, regulation, court order or "
          "a competent authority, or where disclosure is necessary to prevent "
          "fraud or to protect our legal rights."),
         ("Sending data outside the UK",
          "Some of our providers are outside the United Kingdom. Where "
          "personal data is transferred out of the UK we rely on UK adequacy "
          "regulations where they apply, or on the International Data Transfer "
          "Agreement or the UK Addendum to the EU standard contractual clauses "
          "where they do not.")],
        layout="cards")

    S["retention"] = cols(
        "how-long", "Retention", "How long we keep it.",
        "Actual periods rather than “as long as necessary”, which is the "
        "vagueness the ICO most often objects to.",
        [("Order and transaction records",
          "Six years from the end of the financial year in which the order was "
          "placed, to meet HMRC record-keeping requirements."),
         ("Customer service correspondence",
          "Two years, for handling follow-up queries and disputes."),
         ("Marketing consent and email address",
          "Until you unsubscribe, plus a short suppression record afterwards so "
          "we do not email you again once you have asked us not to."),
         ("Analytics and website usage data",
          "Fourteen months.")],
        layout="split", scheme="wash")

    S["rights"] = cols(
        "your-rights", "Your rights", "What you can ask us for.", None,
        [("What you can ask for",
          "Access to the data we hold about you; correction of anything "
          "inaccurate; erasure; restriction of processing; objection to "
          "processing carried out on the basis of legitimate interests; "
          "portability of data you gave us; and withdrawal of consent at any "
          "time where processing relies on it."),
         ("How to exercise them",
          "Email info@hydrosox.com. We will respond within one month. We may "
          "ask you to confirm your identity first, which is a protection for "
          "you rather than an obstacle."),
         ("It is free",
          "There is no charge for making a request, unless a request is "
          "manifestly unfounded or excessive."),
         ("If you are not satisfied",
          "You can complain to the Information Commissioner's Office at "
          "ico.org.uk, or by calling 0303 123 1113. We would rather you came "
          "to us first so we can put it right, but you do not have to.")],
        layout="steps")

    S["security"] = cols(
        "security", "Security and the rest", "Security, children and other sites.",
        None,
        [("Security",
          "We use appropriate technical and organisational measures to protect "
          "personal data. No transmission over the internet is completely "
          "secure and we cannot guarantee absolute security — but we take it "
          "seriously, and we would tell you promptly if something went wrong."),
         ("Children",
          "This site is not intended for children under 16 and we do not "
          "knowingly collect their data. If we become aware that we have, we "
          "will delete it."),
         ("Other websites",
          "Links to other sites are not our responsibility. Their privacy "
          "practices are their own and we would encourage you to read them."),
         ("Changes to this policy",
          "If we change it, the revised version appears here with a new date. "
          "Where a change is significant we will tell you rather than relying "
          "on you to notice.")],
        layout="cards", scheme="wash")

    S["close"] = note(
        "ask", "Anything unclear",
        "A person will explain any of this.",
        ["Data policies are written by people who are used to reading them. If "
         "a sentence here does not tell you what you wanted to know, say so and "
         "we will answer it plainly."],
        scheme="paper",
        footnote="The binding version of this policy is the one published at "
                 "/policies/privacy-policy, which is the text Shopify shows at "
                 "checkout. This page says the same thing in the site's own "
                 "words.",
        cta=("Contact us", "/pages/contact"))

    order = ["crumb", "intro", "who", "collect", "basis", "share",
             "retention", "rights", "security", "close"]
    write("privacy-policy", S, order, "Privacy policy")


# ===========================================================================
def terms():
    S = collections.OrderedDict()
    S["crumb"] = crumb("Terms of service")

    S["intro"] = note(
        "terms", "Terms and conditions",
        "The terms, written to be read.",
        ["These govern your use of this website and anything you buy from us. "
         "Nothing in them reduces your statutory rights as a consumer."],
        heading_tag="h1")

    S["who"] = cols(
        "who-and-use", "Who and how", "Who we are, and using this site.", None,
        [("Who we are",
          "This website is operated by Hydrosox Ltd, a company registered in "
          "England and Wales, with its registered office at 399–405 Oxford "
          "Street, Mayfair, London W1C 2BU. You can contact us at "
          "info@hydrosox.com or on 0203 4322 920."),
         ("Using this website",
          "By using this site you confirm you are at least 18, or have the "
          "consent of a parent or guardian. You agree to use it lawfully, and "
          "not in a way that restricts anyone else's use of it. You must not "
          "attempt to gain unauthorised access, introduce malicious software, "
          "or disrupt the site or its services. We may restrict or end access "
          "if we reasonably suspect misuse.")],
        layout="split")

    S["orders"] = cols(
        "products-and-orders", "Products and orders",
        "What we sell, and when a contract exists.", None,
        [("Product information",
          "We take reasonable care to make sure descriptions, images, "
          "specifications and prices are accurate and current. Minor variation "
          "in colour, texture or appearance can occur through manufacturing "
          "and through differences in screen settings; that is not a defect. "
          "Where we discover an error in a description or a price, we will "
          "tell you before dispatch and you may cancel."),
         ("When a contract is formed",
          "Placing an order is an offer to buy, subject to these terms. All "
          "orders are subject to acceptance and availability. A contract is "
          "formed when we confirm dispatch of your order, not when you place "
          "it."),
         ("When we may refuse an order",
          "We may refuse or cancel an order before dispatch — for suspected "
          "fraud, a pricing or technical error, a stock problem, or a breach "
          "of these terms. If payment has been taken, you receive a full "
          "refund to the original payment method.")],
        layout="steps")

    S["money"] = cols(
        "prices-and-delivery", "Prices and delivery",
        "What you pay, and who carries the risk.", None,
        [("Prices and payment",
          "All prices are in pounds sterling and include VAT. The price shown "
          "when you place your order is the price you pay. We may change "
          "prices at any time, but a change never affects an order already "
          "confirmed. Where a delivery charge applies, the total price "
          "including it is shown before you commit to buying. Payment is taken "
          "in full at the time of purchase, through secure third-party "
          "processors. We do not store full card details."),
         ("Delivery and risk",
          "Delivery timescales are estimates unless we state otherwise. We are "
          "not responsible for delays caused by carriers, customs, weather, "
          "industrial action or other circumstances outside our reasonable "
          "control — but if a parcel is delayed or lost after dispatch we will "
          "work with the carrier to resolve it. Risk in the goods passes to "
          "you when they are delivered to the address you gave at checkout."),
         ("Cancellation, returns and refunds",
          "Your right to cancel a distance sale within 14 days, and your "
          "rights if goods are faulty, are set out in full on our returns "
          "page, which forms part of these terms. Nothing in these terms "
          "limits your rights under the Consumer Rights Act 2015 or the "
          "Consumer Contracts (Information, Cancellation and Additional "
          "Charges) Regulations 2013.")],
        layout="focus", scheme="ink", mirror=True,
        link=("Returns and refunds", "/pages/returns-and-refunds"))

    S["liability"] = cols(
        "liability-and-ip", "Liability", "Liability, property and events.", None,
        [("Our liability to you",
          "We do not exclude or limit our liability for death or personal "
          "injury caused by our negligence, for fraud or fraudulent "
          "misrepresentation, or for anything else that cannot lawfully be "
          "excluded. Subject to that, our liability for any claim arising from "
          "an order is limited to the price you paid for the goods. We are not "
          "liable for losses that were not reasonably foreseeable when the "
          "contract was made."),
         ("Intellectual property",
          "The content of this site — text, images, video, design and trade "
          "marks — belongs to us or is used under licence. You may not "
          "reproduce it commercially without our written permission. Porelle® "
          "is a trade mark of its owner and is used here under licence."),
         ("Things outside our control",
          "We are not liable for failure or delay caused by events outside our "
          "reasonable control, including natural events, war, industrial "
          "action, supply chain disruption or governmental action.")],
        layout="cards")

    S["general"] = cols(
        "general", "General", "Complaints, changes and the governing law.",
        None,
        [("General",
          "If any provision of these terms is found to be invalid, the rest "
          "remain in force. These terms, together with our privacy policy, "
          "cookie policy, returns policy and delivery policy, form the whole "
          "agreement between us. We may update these terms; the version that "
          "applies to your order is the one published when you placed it."),
         ("Complaints",
          "If something has gone wrong, email info@hydrosox.com or phone "
          "0203 4322 920 and we will try to resolve it directly. We are not "
          "currently a member of an alternative dispute resolution scheme. If "
          "we cannot resolve a complaint between us, you retain your right to "
          "bring a claim in the courts."),
         ("Governing law",
          "These terms are governed by the laws of England and Wales, and "
          "disputes are subject to the exclusive jurisdiction of the courts of "
          "England and Wales. If you live in Scotland or Northern Ireland, you "
          "may also bring proceedings in the courts there.")],
        layout="split", scheme="wash")

    S["close"] = note(
        "ask", "If something has gone wrong",
        "Start with a person, not a clause.",
        ["Most things people reach for terms and conditions about are settled "
         "faster by phoning us. The clauses are here because they have to be; "
         "they are not the first thing we would like you to try."],
        footnote="The binding version of these terms is the one published at "
                 "/policies/terms-of-service, which is the text Shopify shows "
                 "at checkout. This page says the same thing in the site's own "
                 "words.",
        cta=("Contact us", "/pages/contact"))

    order = ["crumb", "intro", "who", "orders", "money", "liability",
             "general", "close"]
    write("terms-of-service", S, order, "Terms of service")


if __name__ == "__main__":
    privacy()
    terms()
