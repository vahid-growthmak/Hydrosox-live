/**
 * <hs-buy> — colour, size and quantity-tier selection.
 *
 * Reads the product's real variants from an inline JSON payload, resolves the
 * selected colour + size to a variant id, and keeps the submit button's total,
 * the savings line and availability in step with the chosen tier.
 *
 * Tier totals are derived from the live variant price minus the tier's
 * discount, so they follow a price change in Shopify automatically.
 */

/** Formats cents using the shop's own money format string. */
function formatMoney(cents, format) {
  const value = Number(cents) || 0;

  const withDelimiters = (num, precision, thousands, decimal) => {
    const fixed = (num / 100).toFixed(precision);
    const [whole, fraction] = fixed.split('.');
    const grouped = whole.replace(/(\d)(?=(\d\d\d)+(?!\d))/g, `$1${thousands}`);
    return fraction ? `${grouped}${decimal}${fraction}` : grouped;
  };

  const placeholder = /\{\{\s*(\w+)\s*\}\}/;
  const match = (format || '${{amount}}').match(placeholder);
  if (!match) return format || String(value);

  let formatted;
  switch (match[1]) {
    case 'amount_no_decimals':
      formatted = withDelimiters(value, 0, ',', '.');
      break;
    case 'amount_with_comma_separator':
      formatted = withDelimiters(value, 2, '.', ',');
      break;
    case 'amount_no_decimals_with_comma_separator':
      formatted = withDelimiters(value, 0, '.', ',');
      break;
    case 'amount_with_space_separator':
      formatted = withDelimiters(value, 2, ' ', ',');
      break;
    case 'amount_no_decimals_with_space_separator':
      formatted = withDelimiters(value, 0, ' ', ',');
      break;
    default:
      formatted = withDelimiters(value, 2, ',', '.');
  }

  return (format || '${{amount}}').replace(placeholder, formatted);
}

class HSBuy extends HTMLElement {
  connectedCallback() {
    this.moneyFormat = this.dataset.moneyFormat || '${{amount}}';
    this.colourIndex = parseInt(this.dataset.colourIndex || '0', 10) - 1;
    this.sizeIndex = parseInt(this.dataset.sizeIndex || '0', 10) - 1;

    this.variants = this.readVariants();
    if (!this.variants.length) return;

    this.variantInput = this.querySelector('[data-hs-variant-id]');
    this.quantityInput = this.querySelector('[data-hs-quantity]');
    this.submit = this.querySelector('[data-hs-submit]');
    this.submitLabel = this.querySelector('[data-hs-submit-label]');
    this.submitTotal = this.querySelector('[data-hs-submit-total]');
    this.savings = this.querySelector('[data-hs-savings]');

    // Selection state, seeded from whichever variant the server rendered.
    const initialId = parseInt(this.variantInput?.value || '0', 10);
    const initial = this.variants.find((v) => v.id === initialId) || this.variants[0];
    this.selection = {
      colour: this.colourIndex >= 0 ? initial.options[this.colourIndex] : null,
      size: this.sizeIndex >= 0 ? initial.options[this.sizeIndex] : null,
    };

    this.tier = this.querySelector('[data-hs-tier].is-selected') || this.querySelector('[data-hs-tier]');

    this.guardSwatches();

    /*
      The gallery sits beside this element rather than inside it — the layout
      puts the picture in one column and the form in the other — so it has to be
      looked up from the section, not from `this`. Scoped to the closest .hs-buy
      so two widgets on one page never swap each other's picture.
    */
    this.gallery = this.closest('.hs-buy')?.querySelector('[data-hs-gallery] img') || null;

    this.bindOptions();
    this.bindTiers();
    this.bindGuide();
    this.update();
  }

  /**
   * Keeps the colour swatches intact when a third-party script rewrites them.
   *
   * The Restock Rocket app's collection-page script treats any non-product
   * page as a listing, takes the first button inside the product form to be
   * the buy button, and replaces its contents with the word "Preorder". On
   * every landing page that embeds this widget the first button in the form
   * is the first colour swatch, so the Black swatch lost its dot and label
   * site-wide while the real submit — which the app labels correctly through
   * its own configured script — sat two elements further down.
   *
   * The right place to fix that is the app's own settings; this is the
   * theme's guarantee that its controls stay usable regardless.
   *
   * The clean markup cannot be snapshotted from the DOM: the app runs before
   * this script, so by the time we look the damage is already there and a DOM
   * snapshot would faithfully restore the damage. The pristine swatch comes
   * from the server instead, through the Section Rendering API — the same
   * channel the cart already uses — and is matched back by option value.
   * Restores are capped so a script that reapplies forever gets the last word
   * rather than a spin loop, and the console says who won.
   */
  guardSwatches() {
    const swatches = [...this.querySelectorAll('.hs-buy__swatch')];
    if (!swatches.length || !('MutationObserver' in window)) return;

    const sectionEl = this.closest('.shopify-section');
    const sectionId = sectionEl ? sectionEl.id.replace(/^shopify-section-/, '') : null;

    const snapshots = new Map();
    const healthy = (b) => !!b.querySelector('.hs-buy__swatch-ring');

    const snapshotFrom = (doc) => {
      doc.querySelectorAll('.hs-buy__swatch').forEach((clean) => {
        const value = clean.getAttribute('data-hs-value');
        const mine = swatches.find((b) => b.getAttribute('data-hs-value') === value);
        if (mine && clean.querySelector('.hs-buy__swatch-ring')) {
          snapshots.set(mine, {
            html: clean.innerHTML,
            cls: clean.className.replace(/\bis-selected\b/g, '').trim(),
          });
        }
      });
    };

    let budget = 20;
    let queued = false;

    const repair = () => {
      queued = false;
      swatches.forEach((b) => {
        if (healthy(b)) return;
        const snap = snapshots.get(b);
        if (!snap || budget <= 0) return;
        budget -= 1;
        const selectedNow = b.classList.contains('is-selected');
        b.innerHTML = snap.html;
        b.className = snap.cls;
        b.classList.toggle('is-selected', selectedNow);
        if (budget === 0) {
          console.warn('hs-buy: swatch guard budget exhausted; an external script keeps rewriting the colour swatches.');
        }
      });
    };

    const arm = () => {
      this.swatchGuard = new MutationObserver(() => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(repair);
      });
      swatches.forEach((b) => this.swatchGuard.observe(b, { childList: true, subtree: true, characterData: true }));
      repair();
    };

    if (swatches.every(healthy)) {
      // Nothing damaged yet: the DOM itself is the clean source.
      swatches.forEach((b) => snapshots.set(b, {
        html: b.innerHTML,
        cls: b.className.replace(/\bis-selected\b/g, '').trim(),
      }));
      arm();
      return;
    }

    if (!sectionId || !window.fetch) return;
    fetch(`${window.location.pathname}?sections=${sectionId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        const html = data[sectionId];
        if (!html) return;
        snapshotFrom(new DOMParser().parseFromString(html, 'text/html'));
        arm();
      })
      .catch(() => {
        // Better a rewritten swatch than a broken widget.
      });
  }

  readVariants() {
    const node = this.querySelector('[data-hs-variants]');
    if (!node) return [];
    try {
      return JSON.parse(node.textContent) || [];
    } catch {
      return [];
    }
  }

  /* ------------------------------------------------------------- selection */

  bindOptions() {
    this.querySelectorAll('[data-hs-option]').forEach((button) => {
      button.addEventListener('click', () => {
        const kind = button.dataset.hsOption;
        this.selection[kind] = button.dataset.hsValue;

        // Move the checked state across this group only.
        this.querySelectorAll(`[data-hs-option="${kind}"]`).forEach((sibling) => {
          const on = sibling === button;
          sibling.classList.toggle('is-selected', on);
          sibling.setAttribute('aria-checked', on ? 'true' : 'false');
        });

        this.update();
      });
    });
  }

  bindTiers() {
    this.querySelectorAll('[data-hs-tier]').forEach((button) => {
      button.addEventListener('click', () => {
        this.tier = button;
        this.querySelectorAll('[data-hs-tier]').forEach((sibling) => {
          const on = sibling === button;
          sibling.classList.toggle('is-selected', on);
          sibling.setAttribute('aria-checked', on ? 'true' : 'false');
        });
        this.update();
      });
    });
  }

  currentVariant() {
    return this.variants.find((variant) => {
      if (this.colourIndex >= 0 && variant.options[this.colourIndex] !== this.selection.colour) return false;
      if (this.sizeIndex >= 0 && variant.options[this.sizeIndex] !== this.selection.size) return false;
      return true;
    });
  }

  update() {
    const variant = this.currentVariant();
    const quantity = parseInt(this.tier?.dataset.hsQty || '1', 10);
    const discount = parseInt(this.tier?.dataset.hsDiscount || '0', 10);

    if (this.quantityInput) this.quantityInput.value = String(quantity);
    if (this.variantInput && variant) this.variantInput.value = String(variant.id);

    this.refreshTierPrices(variant);
    this.refreshGallery(variant);

    const unavailable = !variant || !variant.available;

    if (this.submit) {
      this.submit.disabled = unavailable;
      if (this.submitLabel) {
        this.submitLabel.textContent = !variant
          ? this.dataset.labelUnavailable
          : variant.available
            ? this.dataset.labelAdd
            : this.dataset.labelSoldOut;
      }
    }

    if (!variant) {
      if (this.submitTotal) this.submitTotal.textContent = '';
      if (this.savings) this.savings.textContent = '';
      return;
    }

    const gross = variant.price * quantity;
    const net = Math.max(0, gross - discount);

    if (this.submitTotal) {
      this.submitTotal.textContent = variant.available ? formatMoney(net, this.moneyFormat) : '';
    }

    if (this.savings) {
      if (discount > 0 && variant.available) {
        const against = (this.dataset.labelAgainst || 'against __AMOUNT__').replace(
          '__AMOUNT__',
          formatMoney(gross, this.moneyFormat)
        );
        this.savings.textContent = `${this.dataset.labelSave} ${formatMoney(discount, this.moneyFormat)} ${against}`;
      } else {
        this.savings.textContent = '';
      }
    }
  }

  /*
    Show the selected variant's own photograph.

    Nothing happens unless the variant actually carries an image and it differs
    from what is already on screen — otherwise every quantity-tier click would
    reset src and make the browser re-decode the same file.

    `sizes` is left alone: it is a description of the layout, not of the file,
    and the layout has not changed.
  */
  refreshGallery(variant) {
    const img = this.gallery;
    if (!img || !variant || !variant.image) return;
    if (img.getAttribute('src') === variant.image) return;

    img.setAttribute('src', variant.image);
    if (variant.srcset) img.setAttribute('srcset', variant.srcset);
    if (variant.alt) img.setAttribute('alt', variant.alt);
  }

  // Tier rows show the price of the variant actually selected.
  refreshTierPrices(variant) {
    if (!variant) return;
    this.querySelectorAll('[data-hs-tier]').forEach((row) => {
      const qty = parseInt(row.dataset.hsQty || '1', 10);
      const discount = parseInt(row.dataset.hsDiscount || '0', 10);
      const net = Math.max(0, variant.price * qty - discount);

      const total = row.querySelector('.hs-buy__tier-total');
      if (total) total.textContent = formatMoney(net, this.moneyFormat);

      const unit = row.querySelector('.hs-buy__tier-unit');
      if (unit && qty > 1) {
        unit.textContent = `${formatMoney(Math.round(net / qty), this.moneyFormat)} ${
          this.dataset.labelPerUnit || ''
        }`.trim();
      }

      const save = row.querySelector('.hs-buy__tier-save');
      if (save && discount > 0) {
        save.textContent = `${this.dataset.labelSave} ${formatMoney(discount, this.moneyFormat)}`;
      }
    });
  }

  /* ----------------------------------------------------------- size guide */

  bindGuide() {
    const dialog = this.closest('section')?.querySelector('[data-hs-guide]');
    if (!dialog) return;

    this.closest('section')
      ?.querySelectorAll('[data-hs-guide-open]')
      .forEach((button) =>
        button.addEventListener('click', () => {
          if (typeof dialog.showModal === 'function') dialog.showModal();
          else dialog.setAttribute('open', '');
        })
      );

    dialog.querySelectorAll('[data-hs-guide-close]').forEach((button) =>
      button.addEventListener('click', () => {
        if (typeof dialog.close === 'function') dialog.close();
        else dialog.removeAttribute('open');
      })
    );

    // Clicking the backdrop closes it, matching the rest of the site's overlays.
    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) dialog.close();
    });
  }
}

if (!customElements.get('hs-buy')) customElements.define('hs-buy', HSBuy);
