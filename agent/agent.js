import { chromium } from 'playwright';
import OpenAI from 'openai';

const MESSAGE = process.env.MESSAGE || 'Xin chào';
const PROFILE = process.env.CHATGPT_PROFILE || './chatgpt-profile';
const URL = process.env.CHATGPT_URL || 'https://chatgpt.com/';

const openai = process.env.OPENAI_API_KEY ? new OpenAI() : null;

async function findComposer(page) {
  const candidates = [
    page.locator('textarea').first(),
    page.locator('[contenteditable="true"]').first(),
    page.getByRole('textbox').first(),
  ];
  for (const c of candidates) {
    if (await c.count() && await c.isVisible().catch(() => false)) return c;
  }
  return null;
}

async function findSend(page) {
  const candidates = [
    page.getByRole('button', { name: /send|gửi/i }).last(),
    page.locator('button[data-testid*="send"]').last(),
    page.locator('button').filter({ has: page.locator('svg') }).last(),
  ];
  for (const c of candidates) {
    if (await c.count() && await c.isVisible().catch(() => false)) return c;
  }
  return null;
}

async function aiLocate(page) {
  if (!openai) return null;
  const png = await page.screenshot({ type: 'png' });
  const response = await openai.responses.create({
    model: process.env.OPENAI_MODEL || 'gpt-5.6-luna',
    input: [{ role: 'user', content: [
      { type: 'input_text', text: 'Inspect this screenshot of ChatGPT. Return JSON only: {"composer": {"x": number, "y": number}, "send": {"x": number, "y": number}}. Coordinates are pixel coordinates from the top-left. If a target is not visible, set it to null. Do not click anything.' },
      { type: 'input_image', image_url: `data:image/png;base64,${png.toString('base64')}` }
    ] }]
  });
  const text = response.output_text.match(/\{[\s\S]*\}/)?.[0];
  return text ? JSON.parse(text) : null;
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ storageState: undefined });
const page = await context.newPage();
await page.goto(URL, { waitUntil: 'domcontentloaded' });

console.log('ChatGPT opened. Complete login once in the persistent VPS browser profile before running unattended.');

let composer = await findComposer(page);
if (!composer) {
  const ai = await aiLocate(page);
  if (ai?.composer) {
    await page.mouse.click(ai.composer.x, ai.composer.y);
  }
  composer = await findComposer(page);
}
if (!composer) throw new Error('Could not locate the ChatGPT message composer.');

await composer.click();
await page.keyboard.insertText(MESSAGE);

let send = await findSend(page);
if (send) {
  await send.click();
} else {
  const ai = await aiLocate(page);
  if (!ai?.send) throw new Error('Could not locate the Send button.');
  await page.mouse.click(ai.send.x, ai.send.y);
}

console.log('Message submitted.');
await page.waitForTimeout(Number(process.env.WAIT_MS || 1500));
await browser.close();
