// ==UserScript==
// @name         Google Cleaner: Remove Sponsored & Redirects
// @namespace    https://github.com/shiltian/my-utils/tree/main/userscripts
// @version      2.0
// @description  Removes sponsored (ad) links and Google's redirect tracking from search results
// @author       Shilei Tian
// @match        https://www.google.com/*
// @match        https://www.google.co.uk/*
// @match        https://www.google.ca/*
// @match        https://www.google.de/*
// @match        https://www.google.fr/*
// @match        https://www.google.es/*
// @match        https://www.google.it/*
// @match        https://www.google.com.au/*
// @match        https://www.google.co.in/*
// @match        https://www.google.co.jp/*
// @match        https://www.google.com.br/*
// @match        https://www.google.nl/*
// @match        https://www.google.pl/*
// @match        https://www.google.com.mx/*
// @match        https://www.google.ru/*
// @include      /^https:\/\/www\.google\.[a-z.]+\/.*$/
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Utility function to remove sponsored/ad links
    function removeSponsoredLinks() {
        // Google Ads have different selectors, but commonly:
        // - Top and bottom ads: div[data-testid="ad"] or div[aria-label="Ads"]
        // - Sometimes have a label "Sponsored" or "Ad"
        // We'll try to cover major selectors
        const adSelectors = [
            'div[data-text-ad="1"]',    // Modern text ads
            'div[data-text-ad]',        // Old ads
            'div[aria-label="Ads"]',    // Some ad containers
            'div[data-testid="ad"]',    // Mobile
            'div[aria-label="Sponsored"]'
        ];

        // Fallback: Remove search results with a clear ad marker
        const allResults = document.querySelectorAll('div.g, div.ads-ad, div.uEierd, div.v5yQqb');

        allResults.forEach(result => {
            // Try to find an 'Ad', 'Sponsored', or 'Sponsored result' label within the result
            const adLabel = Array.from(result.querySelectorAll('span, div, abbr')).find(
                el => el.textContent.trim().match(/^(Ad|Sponsored(\s+result)?)$/i)
            );
            if (adLabel) {
                result.remove();
            }
        });

        // Remove with explicit selectors
        adSelectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(adBlock => adBlock.remove());
        });
    }

    // Utility function to de-redirect Google result links
    function fixRedirectLinks() {
        // Search result links have a data-sb attribute that contains the redirect URL
        // The href starts clean but Google rewrites it on interaction
        const searchResultLinks = document.querySelectorAll('a[data-sb]');

        searchResultLinks.forEach(a => {
            // Skip if already processed
            if (a.dataset.cleanedLink) return;

            // The href should already be clean, but let's verify
            const currentHref = a.href;

            // If href is already clean (not a redirect), protect it
            if (currentHref && !currentHref.includes('/url?')) {
                const realHref = currentHref;

                // Store the real URL
                a.dataset.realHref = realHref;
                a.dataset.cleanedLink = 'true';

                // Store original href getter/setter
                const originalHrefDescriptor = Object.getOwnPropertyDescriptor(HTMLAnchorElement.prototype, 'href');

                // Remove tracking attributes and the data-sb that Google uses to rewrite
                a.removeAttribute('onmousedown');
                a.removeAttribute('data-ved');
                a.removeAttribute('ping');
                a.removeAttribute('data-sb'); // Remove the redirect URL source

                // Add event listeners to prevent Google from rewriting the URL
                const protectLink = (e) => {
                    // Stop the event from reaching Google's handlers
                    e.stopImmediatePropagation();

                    // Restore href if it was changed
                    const currentHref = originalHrefDescriptor.get.call(a);
                    if (currentHref !== realHref) {
                        originalHrefDescriptor.set.call(a, realHref);
                    }
                };

                // Capture key events that Google uses to rewrite URLs
                // Use capturing phase (true) to intercept before Google's handlers
                ['mousedown', 'contextmenu', 'click', 'touchstart'].forEach(eventType => {
                    a.addEventListener(eventType, protectLink, true);
                });

                // Override href property to prevent direct modification
                Object.defineProperty(a, 'href', {
                    get: function() {
                        return realHref;
                    },
                    set: function(value) {
                        // Ignore any attempts to change the href
                        return realHref;
                    },
                    configurable: true
                });

                // Set initial href
                originalHrefDescriptor.set.call(a, realHref);
            }
        });
    }

    // Run on initial page load
    function cleanGoogle() {
        removeSponsoredLinks();
        fixRedirectLinks();
    }

    // Run after navigating or updating results (SPA)
    const observer = new MutationObserver(() => {
        cleanGoogle();
    });

    // Start observing the document for dynamically added results/ads
    observer.observe(document.body, { childList: true, subtree: true });

    // Initial clean
    cleanGoogle();

    // Also clean whenever the user scrolls (sometimes lazy loaded ads/links appear)
    window.addEventListener('scroll', cleanGoogle, { passive: true });
})();
