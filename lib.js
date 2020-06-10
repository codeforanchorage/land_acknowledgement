const puppeteer = require('puppeteer');

async function getLandText(location) {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();

  const MODAL_BUTTON_SELECTOR = '.modal-footer > button';
  const SEARCH_SELECTOR = 'input[placeholder=Search]';
  const LOCATION_SELECTOR = 'li.active';
  const RESULTS_SELECTOR = '.results-tab';

  await page.goto('https://native-land.ca/');
  await page.click(MODAL_BUTTON_SELECTOR);
  await page.waitFor(2000);

  await page.click(SEARCH_SELECTOR);
  await page.keyboard.type(location);
  await page.waitForSelector(LOCATION_SELECTOR);

  await page.click(LOCATION_SELECTOR);

  // If certain elements on the page haven't finished loading before we do the search,
  // then the location data won't actually display.
  // This loop retries the search until a result is given.
  while (!await page.$(`${RESULTS_SELECTOR} > p`)) {
    await page.waitFor(500);
    await page.click(SEARCH_SELECTOR);
    await page.keyboard.type(location);
    await page.waitForSelector(LOCATION_SELECTOR);

    await page.click(LOCATION_SELECTOR);
  }

  const addressElement = await page.$(SEARCH_SELECTOR);
  const address = await addressElement.evaluate(element => element.value);
  const resultElement = await page.$(RESULTS_SELECTOR);
  const resultText = await resultElement.evaluate(element => element.innerText);

  const text = `${address} is on the land of: ${resultText.substring(resultText.indexOf('\n'))}`;

  await browser.close();

  return text;
}

module.exports = {
    getLandText
}