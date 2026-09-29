/**
 * BrewMart analytics helper.
 *
 * Wraps GA4 (window.gtag) and Meta Pixel (window.fbq) so the rest of the
 * site never has to check "is tracking even configured" -- both calls are
 * no-ops when GOOGLE_ANALYTICS_ID / FACEBOOK_PIXEL_ID aren't set, since
 * base.html then never defines gtag/fbq in the first place.
 *
 * Three things are tracked automatically, with no per-page wiring beyond
 * a few data-* attributes:
 *   1. Impressions  -- every ".product-card[data-product-id]" present on a
 *      page load fires one GA4 "view_item_list" event (product listing,
 *      home page sections, related-product rails, etc. -- anywhere
 *      products/card.html is used).
 *   2. Clicks       -- clicking into a product card fires GA4 "select_item"
 *      for that one product.
 *   3. Conversions   -- "view_item" fires on the product detail page;
 *      "add_to_cart" / "purchase" fire from a one-time JSON payload a view
 *      rendered into #ecommerce-event-data (see
 *      core.context_processors.pending_ecommerce_event and the purchase
 *      payload built in orders/analytics.py).
 */
(function () {
    "use strict";

    function safeGtag() {
        if (typeof window.gtag === "function") {
            window.gtag.apply(window, arguments);
        }
    }

    function safeFbq() {
        if (typeof window.fbq === "function") {
            window.fbq.apply(window, arguments);
        }
    }

    function productDataFromEl(el) {
        var price = parseFloat(el.getAttribute("data-product-price"));
        return {
            item_id: el.getAttribute("data-product-id"),
            item_name: el.getAttribute("data-product-name") || undefined,
            item_category: el.getAttribute("data-product-category") || undefined,
            price: isNaN(price) ? undefined : price,
            currency: el.getAttribute("data-product-currency") || "NPR",
            quantity: 1,
        };
    }

    function trackListImpressionsAndClicks() {
        var cards = document.querySelectorAll(".product-card[data-product-id]");
        if (!cards.length) {
            return;
        }

        var items = [];
        cards.forEach(function (card) {
            items.push(productDataFromEl(card));
        });
        safeGtag("event", "view_item_list", {
            item_list_name: document.title,
            items: items,
        });

        cards.forEach(function (card) {
            var links = card.querySelectorAll("a[href]");
            links.forEach(function (link) {
                link.addEventListener("click", function () {
                    safeGtag("event", "select_item", { items: [productDataFromEl(card)] });
                });
            });
        });
    }

    function trackProductDetailView() {
        var el = document.querySelector("#product-detail[data-product-id]");
        if (!el) {
            return;
        }
        var data = productDataFromEl(el);
        safeGtag("event", "view_item", {
            currency: data.currency,
            value: data.price,
            items: [data],
        });
        safeFbq("track", "ViewContent", {
            content_ids: [data.item_id],
            content_name: data.item_name,
            content_category: data.item_category,
            value: data.price,
            currency: data.currency,
        });
    }

    function fireQueuedEcommerceEvent() {
        var el = document.getElementById("ecommerce-event-data");
        if (!el) {
            return;
        }
        var payload;
        try {
            payload = JSON.parse(el.textContent);
        } catch (e) {
            return;
        }
        if (!payload || !payload.event) {
            return;
        }

        var gaParams = {};
        Object.keys(payload).forEach(function (key) {
            if (key !== "event" && key !== "fb_event") {
                gaParams[key] = payload[key];
            }
        });
        safeGtag("event", payload.event, gaParams);

        if (payload.fb_event) {
            var items = payload.items || [];
            safeFbq("track", payload.fb_event, {
                value: payload.value,
                currency: payload.currency,
                content_type: "product",
                content_ids: items.map(function (item) {
                    return item.item_id;
                }),
                contents: items.map(function (item) {
                    return { id: item.item_id, quantity: item.quantity || 1 };
                }),
            });
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        trackListImpressionsAndClicks();
        trackProductDetailView();
        fireQueuedEcommerceEvent();
    });
})();
