// Print an HTML page to PDF with Chromium (tools/build_deliverables.py calls it).
//   node tools/pdf_print.js page.html out.pdf [packet|landscape]
// packet: Letter, page numbers and the title in the footer; landscape: one
// drawing per Letter landscape page.
const path = require("path");
const { chromium } = require("playwright");

(async () => {
  const [src, out, mode = "packet", title = ""] = process.argv.slice(2);
  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
  }
  const page = await browser.newPage();
  await page.goto("file://" + path.resolve(src), { waitUntil: "load" });
  const opts = { path: out, format: "Letter", printBackground: true, preferCSSPageSize: true };
  if (mode === "landscape") {
    opts.landscape = true;
    opts.margin = { top: "0.4in", bottom: "0.4in", left: "0.4in", right: "0.4in" };
  } else {
    opts.displayHeaderFooter = true;
    opts.headerTemplate = "<span></span>";
    opts.footerTemplate =
      '<div style="font-size:8px;width:100%;padding:0 0.6in;color:#777;display:flex;justify-content:space-between;' +
      'font-family:Helvetica,Arial,sans-serif"><span>' + title + '</span>' +
      '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>';
    opts.margin = { top: "0.6in", bottom: "0.7in", left: "0.6in", right: "0.6in" };
  }
  await page.pdf(opts);
  await browser.close();
})();
