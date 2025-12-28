// ==UserScript==
// @name         ROCm CI Manifest Navigator
// @namespace    https://github.com/shiltian/my-utils/tree/main/userscripts
// @version      2.2
// @description  Adds Previous/Next/Compare buttons to navigate and compare build manifests on ROCm CI
// @author       Shilei Tian
// @match        http://rocm-ci.amd.com/*/artifact/manifest.xml
// @run-at       document-end
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Extract build number from URL
    // URL format: http://rocm-ci.amd.com/.../BUILD_NUMBER/artifact/manifest.xml
    const url = window.location.href;
    const match = url.match(/^(.*\/)(\d+)(\/artifact\/manifest\.xml)$/);

    if (!match) {
        console.log('ROCm CI Manifest Navigator: Could not parse build number from URL');
        return;
    }

    const baseUrl = match[1];
    const buildNumber = parseInt(match[2], 10);
    const suffix = match[3];
    const buildPageUrl = `${baseUrl}${buildNumber}`;

    // Helper to create HTML elements in XML document using DOMParser
    function createHTMLElement(htmlString) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlString, 'text/html');
        return doc.body.firstChild;
    }

    // Button style template
    const buttonBaseStyle = `
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        color: white;
        flex: 1;
    `;

    // Create navigation container with two rows
    const containerHTML = `
        <div id="rocm-nav-container" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div style="display: flex; gap: 10px;">
                <button id="rocm-nav-prev" style="${buttonBaseStyle}
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                ">\u2190 Previous (${buildNumber - 1})</button>
                <button id="rocm-nav-next" style="${buttonBaseStyle}
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                ">Next (${buildNumber + 1}) \u2192</button>
            </div>
            <div style="display: flex; gap: 10px;">
                <button id="rocm-nav-back" style="${buttonBaseStyle}
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                ">\u2934 Go Back</button>
                <button id="rocm-nav-compare" style="${buttonBaseStyle}
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                ">\u2696 Compare...</button>
            </div>
        </div>
    `;

    // Create modal HTML
    const modalHTML = `
        <div id="rocm-compare-modal" style="
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                min-width: 320px;
            ">
                <h3 style="margin: 0 0 16px 0; color: #333; font-size: 18px;">
                    Compare Build ${buildNumber} with:
                </h3>
                <input id="rocm-compare-input" type="number" value="${buildNumber - 1}" style="
                    width: 100%;
                    padding: 12px;
                    font-size: 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    box-sizing: border-box;
                    outline: none;
                    transition: border-color 0.2s;
                " placeholder="Enter build number" />
                <div style="display: flex; gap: 10px; margin-top: 16px; justify-content: flex-end;">
                    <button id="rocm-compare-cancel" style="
                        padding: 10px 20px;
                        font-size: 14px;
                        border: 2px solid #e0e0e0;
                        border-radius: 6px;
                        background: white;
                        color: #666;
                        cursor: pointer;
                        transition: all 0.2s;
                    ">Cancel</button>
                    <button id="rocm-compare-submit" style="
                        padding: 10px 20px;
                        font-size: 14px;
                        border: none;
                        border-radius: 6px;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        cursor: pointer;
                        transition: all 0.2s;
                    ">Compare</button>
                </div>
            </div>
        </div>
    `;

    // Find the appropriate parent to append to
    const parent = document.body || document.documentElement;
    if (!parent) {
        console.log('ROCm CI Manifest Navigator: Could not find parent element');
        return;
    }

    // Parse and append elements
    const container = createHTMLElement(containerHTML);
    const modal = createHTMLElement(modalHTML);

    // Import nodes into the current document (needed for XML documents)
    const importedContainer = document.importNode(container, true);
    const importedModal = document.importNode(modal, true);

    parent.appendChild(importedContainer);
    parent.appendChild(importedModal);

    // Get element references (need to query from document after appending)
    const prevButton = document.getElementById('rocm-nav-prev');
    const nextButton = document.getElementById('rocm-nav-next');
    const backButton = document.getElementById('rocm-nav-back');
    const compareButton = document.getElementById('rocm-nav-compare');
    const compareModal = document.getElementById('rocm-compare-modal');
    const compareInput = document.getElementById('rocm-compare-input');
    const compareCancelBtn = document.getElementById('rocm-compare-cancel');
    const compareSubmitBtn = document.getElementById('rocm-compare-submit');

    // Hover effect helper
    function addHoverEffect(btn, shadowColor) {
        if (!btn) return;
        btn.addEventListener('mouseenter', () => {
            btn.style.transform = 'translateY(-2px)';
            btn.style.boxShadow = `0 4px 12px ${shadowColor}`;
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = 'translateY(0)';
            btn.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
        });
    }

    // Add hover effects
    addHoverEffect(prevButton, 'rgba(102, 126, 234, 0.4)');
    addHoverEffect(nextButton, 'rgba(17, 153, 142, 0.4)');
    addHoverEffect(backButton, 'rgba(79, 172, 254, 0.4)');
    addHoverEffect(compareButton, 'rgba(245, 87, 108, 0.4)');

    // Navigation handlers
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            if (buildNumber > 1) {
                window.location.href = `${baseUrl}${buildNumber - 1}${suffix}`;
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => {
            window.location.href = `${baseUrl}${buildNumber + 1}${suffix}`;
        });
    }

    if (backButton) {
        backButton.addEventListener('click', () => {
            window.location.href = buildPageUrl;
        });
    }

    // Compare modal handlers
    if (compareButton && compareModal) {
        compareButton.addEventListener('click', () => {
            compareModal.style.display = 'block';
            compareInput.focus();
            compareInput.select();
        });

        compareModal.addEventListener('click', (e) => {
            if (e.target === compareModal) {
                compareModal.style.display = 'none';
            }
        });

        compareCancelBtn.addEventListener('click', () => {
            compareModal.style.display = 'none';
        });

        compareInput.addEventListener('focus', () => {
            compareInput.style.borderColor = '#f5576c';
        });

        compareInput.addEventListener('blur', () => {
            compareInput.style.borderColor = '#e0e0e0';
        });

        compareInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                performComparison();
            } else if (e.key === 'Escape') {
                compareModal.style.display = 'none';
            }
        });

        compareSubmitBtn.addEventListener('click', performComparison);
    }

    // Simple diff algorithm
    function computeDiff(oldLines, newLines) {
        const oldLen = oldLines.length;
        const newLen = newLines.length;

        // LCS-based diff
        const dp = Array(oldLen + 1).fill(null).map(() => Array(newLen + 1).fill(0));

        for (let i = 1; i <= oldLen; i++) {
            for (let j = 1; j <= newLen; j++) {
                if (oldLines[i - 1] === newLines[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        // Backtrack to find diff
        let i = oldLen, j = newLen;
        const result = [];

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
                result.unshift({ type: 'equal', oldLine: i, newLine: j, text: oldLines[i - 1] });
                i--; j--;
            } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
                result.unshift({ type: 'add', newLine: j, text: newLines[j - 1] });
                j--;
            } else {
                result.unshift({ type: 'remove', oldLine: i, text: oldLines[i - 1] });
                i--;
            }
        }

        return result;
    }

    // Generate diff HTML page
    function generateDiffPage(build1, build2, xml1, xml2) {
        const lines1 = xml1.split('\n');
        const lines2 = xml2.split('\n');
        const diff = computeDiff(lines1, lines2);

        const escapeHtml = (str) => str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');

        let leftHtml = '';
        let rightHtml = '';
        let changeCount = 0;

        for (const item of diff) {
            if (item.type === 'equal') {
                leftHtml += '<div class="line equal"><span class="line-num">' + item.oldLine + '</span><span class="line-content">' + escapeHtml(item.text) + '</span></div>';
                rightHtml += '<div class="line equal"><span class="line-num">' + item.newLine + '</span><span class="line-content">' + escapeHtml(item.text) + '</span></div>';
            } else if (item.type === 'remove') {
                leftHtml += '<div class="line removed"><span class="line-num">' + item.oldLine + '</span><span class="line-content">' + escapeHtml(item.text) + '</span></div>';
                rightHtml += '<div class="line empty"><span class="line-num"></span><span class="line-content"></span></div>';
                changeCount++;
            } else if (item.type === 'add') {
                leftHtml += '<div class="line empty"><span class="line-num"></span><span class="line-content"></span></div>';
                rightHtml += '<div class="line added"><span class="line-num">' + item.newLine + '</span><span class="line-content">' + escapeHtml(item.text) + '</span></div>';
                changeCount++;
            }
        }

        return '<!DOCTYPE html>\n' +
'<html>\n' +
'<head>\n' +
'    <meta charset="UTF-8">\n' +
'    <title>Diff: Build ' + build1 + ' vs ' + build2 + '</title>\n' +
'    <style>\n' +
'        * { margin: 0; padding: 0; box-sizing: border-box; }\n' +
'        body {\n' +
'            font-family: "SF Mono", "Fira Code", "Consolas", monospace;\n' +
'            background: #1e1e2e;\n' +
'            color: #cdd6f4;\n' +
'            min-height: 100vh;\n' +
'        }\n' +
'        .header {\n' +
'            background: linear-gradient(135deg, #313244 0%, #45475a 100%);\n' +
'            padding: 16px 24px;\n' +
'            display: flex;\n' +
'            align-items: center;\n' +
'            justify-content: space-between;\n' +
'            border-bottom: 1px solid #45475a;\n' +
'            position: sticky;\n' +
'            top: 0;\n' +
'            z-index: 100;\n' +
'        }\n' +
'        .header h1 {\n' +
'            font-size: 18px;\n' +
'            font-weight: 600;\n' +
'            color: #cdd6f4;\n' +
'        }\n' +
'        .header .stats {\n' +
'            display: flex;\n' +
'            gap: 16px;\n' +
'            align-items: center;\n' +
'        }\n' +
'        .header .stat {\n' +
'            padding: 6px 12px;\n' +
'            border-radius: 6px;\n' +
'            font-size: 13px;\n' +
'            font-weight: 500;\n' +
'        }\n' +
'        .stat.changes { background: #45475a; color: #f9e2af; }\n' +
'        .diff-container {\n' +
'            display: flex;\n' +
'            overflow: hidden;\n' +
'        }\n' +
'        .diff-panel {\n' +
'            flex: 1;\n' +
'            overflow-x: auto;\n' +
'            overflow-y: scroll;\n' +
'            height: calc(100vh - 60px);\n' +
'        }\n' +
'        .diff-panel:first-child {\n' +
'            border-right: 2px solid #45475a;\n' +
'        }\n' +
'        .panel-header {\n' +
'            background: #313244;\n' +
'            padding: 12px 16px;\n' +
'            font-size: 14px;\n' +
'            font-weight: 600;\n' +
'            color: #89b4fa;\n' +
'            position: sticky;\n' +
'            top: 0;\n' +
'            z-index: 10;\n' +
'            border-bottom: 1px solid #45475a;\n' +
'        }\n' +
'        .line {\n' +
'            display: flex;\n' +
'            min-height: 22px;\n' +
'            line-height: 22px;\n' +
'            font-size: 13px;\n' +
'        }\n' +
'        .line-num {\n' +
'            width: 60px;\n' +
'            min-width: 60px;\n' +
'            text-align: right;\n' +
'            padding-right: 12px;\n' +
'            color: #6c7086;\n' +
'            user-select: none;\n' +
'            background: rgba(0, 0, 0, 0.15);\n' +
'        }\n' +
'        .line-content {\n' +
'            flex: 1;\n' +
'            padding-left: 12px;\n' +
'            white-space: pre;\n' +
'        }\n' +
'        .line.equal { background: transparent; }\n' +
'        .line.added {\n' +
'            background: rgba(166, 227, 161, 0.15);\n' +
'        }\n' +
'        .line.added .line-num { background: rgba(166, 227, 161, 0.25); color: #a6e3a1; }\n' +
'        .line.added .line-content { color: #a6e3a1; }\n' +
'        .line.removed {\n' +
'            background: rgba(243, 139, 168, 0.15);\n' +
'        }\n' +
'        .line.removed .line-num { background: rgba(243, 139, 168, 0.25); color: #f38ba8; }\n' +
'        .line.removed .line-content { color: #f38ba8; }\n' +
'        .line.empty {\n' +
'            background: rgba(0, 0, 0, 0.1);\n' +
'        }\n' +
'        .line.empty .line-num { background: rgba(0, 0, 0, 0.2); }\n' +
'        .diff-panel::-webkit-scrollbar { width: 10px; }\n' +
'        .diff-panel::-webkit-scrollbar-track { background: #1e1e2e; }\n' +
'        .diff-panel::-webkit-scrollbar-thumb { background: #45475a; border-radius: 5px; }\n' +
'        .diff-panel::-webkit-scrollbar-thumb:hover { background: #585b70; }\n' +
'        .nav-hint {\n' +
'            position: fixed;\n' +
'            bottom: 20px;\n' +
'            left: 50%;\n' +
'            transform: translateX(-50%);\n' +
'            background: #313244;\n' +
'            padding: 8px 16px;\n' +
'            border-radius: 8px;\n' +
'            font-size: 12px;\n' +
'            color: #a6adc8;\n' +
'            border: 1px solid #45475a;\n' +
'        }\n' +
'        .nav-hint kbd {\n' +
'            background: #45475a;\n' +
'            padding: 2px 6px;\n' +
'            border-radius: 4px;\n' +
'            margin: 0 2px;\n' +
'        }\n' +
'    </style>\n' +
'</head>\n' +
'<body>\n' +
'    <div class="header">\n' +
'        <h1>\u2696 Manifest Diff: Build ' + build1 + ' \u2192 Build ' + build2 + '</h1>\n' +
'        <div class="stats">\n' +
'            <span class="stat changes">' + changeCount + ' changes</span>\n' +
'        </div>\n' +
'    </div>\n' +
'    <div class="diff-container">\n' +
'        <div class="diff-panel" id="left-panel">\n' +
'            <div class="panel-header">\uD83D\uDCC4 Build ' + build1 + ' (' + lines1.length + ' lines)</div>\n' +
'            ' + leftHtml + '\n' +
'        </div>\n' +
'        <div class="diff-panel" id="right-panel">\n' +
'            <div class="panel-header">\uD83D\uDCC4 Build ' + build2 + ' (' + lines2.length + ' lines)</div>\n' +
'            ' + rightHtml + '\n' +
'        </div>\n' +
'    </div>\n' +
'    <div class="nav-hint">\n' +
'        <kbd>\u2191</kbd><kbd>\u2193</kbd> Scroll &nbsp;|&nbsp; Panels scroll in sync\n' +
'    </div>\n' +
'    <script>\n' +
'        var leftPanel = document.getElementById("left-panel");\n' +
'        var rightPanel = document.getElementById("right-panel");\n' +
'        var isSyncing = false;\n' +
'        leftPanel.addEventListener("scroll", function() {\n' +
'            if (isSyncing) return;\n' +
'            isSyncing = true;\n' +
'            rightPanel.scrollTop = leftPanel.scrollTop;\n' +
'            isSyncing = false;\n' +
'        });\n' +
'        rightPanel.addEventListener("scroll", function() {\n' +
'            if (isSyncing) return;\n' +
'            isSyncing = true;\n' +
'            leftPanel.scrollTop = rightPanel.scrollTop;\n' +
'            isSyncing = false;\n' +
'        });\n' +
'    </script>\n' +
'</body>\n' +
'</html>';
    }

    // Perform the comparison
    async function performComparison() {
        const targetBuild = parseInt(compareInput.value, 10);

        if (isNaN(targetBuild) || targetBuild < 1) {
            alert('Please enter a valid build number');
            return;
        }

        if (targetBuild === buildNumber) {
            alert('Cannot compare a build with itself');
            return;
        }

        // Update button to show loading
        const originalText = compareSubmitBtn.textContent;
        compareSubmitBtn.textContent = 'Loading...';
        compareSubmitBtn.disabled = true;

        try {
            const url1 = `${baseUrl}${buildNumber}${suffix}`;
            const url2 = `${baseUrl}${targetBuild}${suffix}`;

            const [response1, response2] = await Promise.all([
                fetch(url1),
                fetch(url2)
            ]);

            if (!response1.ok) {
                throw new Error(`Failed to fetch build ${buildNumber}: ${response1.status}`);
            }
            if (!response2.ok) {
                throw new Error(`Failed to fetch build ${targetBuild}: ${response2.status}`);
            }

            const xml1 = await response1.text();
            const xml2 = await response2.text();

            // Generate diff page
            const diffHtml = generateDiffPage(buildNumber, targetBuild, xml1, xml2);

            // Open in new tab
            const blob = new Blob([diffHtml], { type: 'text/html' });
            const blobUrl = URL.createObjectURL(blob);
            window.open(blobUrl, '_blank');

            // Close modal
            compareModal.style.display = 'none';

        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            compareSubmitBtn.textContent = originalText;
            compareSubmitBtn.disabled = false;
        }
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ignore if modal is open or typing in input
        if (compareModal.style.display === 'block') return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        // Left arrow or 'p' for previous
        if (e.key === 'ArrowLeft' || e.key === 'p' || e.key === 'P') {
            if (buildNumber > 1) {
                window.location.href = `${baseUrl}${buildNumber - 1}${suffix}`;
            }
        }
        // Right arrow or 'n' for next
        if (e.key === 'ArrowRight' || e.key === 'n' || e.key === 'N') {
            window.location.href = `${baseUrl}${buildNumber + 1}${suffix}`;
        }
        // 'b' or Backspace for go back to build page
        if (e.key === 'b' || e.key === 'B' || e.key === 'Backspace') {
            e.preventDefault();
            window.location.href = buildPageUrl;
        }
        // 'c' for compare
        if (e.key === 'c' || e.key === 'C') {
            compareModal.style.display = 'block';
            compareInput.focus();
            compareInput.select();
        }
    });
})();
