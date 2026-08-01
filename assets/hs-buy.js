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

    this.bindOptions();
    this.bindTiers();
    this.bindGuide();
    this.update();
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
