import { chromium } from 'playwright';
import OpenAI from 'openai';

const MESSAGE = process.env.MESSAGE || 'Xin chào';
const PROFILE = process.env.CHATGPT_PROFILE || './chatgpt-profile';
const URL = process.env.CHATGPT_URL || 'https://chatgpt.com/';
const openai = process.env.OPENAI_API_KEY ? new OpenAI() : null;

async function findComposer(page) {
  for (const c of [page.locator('textarea').first(), page.locator('[contenteditable="true"]').first(), page.getByRole('textbox').first()]) {
    if (await c.count() && await c.isVisible().catch(() => false)) return c;
  }
  return null;
}

async function findSend(page) {
  for (const c of [page.getByRole('button', { name: /send|gửi/i }).last(), page.locator('button[data-testid*="send"]').last()]) {
    if (await c.count() && await c.isVisible().catch(() => false)) return c;
  }
  return null;
}

async function aiLocate(page) {
  if (!openai) return null;
  const png = await page.screenshot({ type: 'png' });
  const r = await openai.responses.create({
    model: process.env.OPENAI_MODEL || 'gpt-5.6-luna',
    input: [{ role: 'user', content: [
      { type: 'input_text', text: 'Inspect this ChatGPT screenshot. Return JSON only: {"composer":{"x":number,"y":number},"send":{"x":number,"y":number}}. Coordinates are pixels from top-left. Use null when not visible.' },
      { type: 'input_image', image_url: `data:image/png;base64,${png.toString('base64')}` }
    ] }]
  });
  const text = r.output_text.match(/\{[\s\S]*\}/)?.[0];
  return text ? JSON.parse(text) : null;
}

const context = await chromium.launchPersistentContext(PROFILE, { headless: true });
const page = await context.newPage();
await page.goto(URL, { waitUntil: 'domcontentloaded' });

let composer = await findComposer(page);
if (!composer) {
  const ai = await aiLocate(page);
  if (ai?.composer) await page.mouse.click(ai.composer.x, ai.composer.y);
  composer = await findComposer(page);
}
if (!composer) throw new Error('Message composer not found. Log in manually once and retry.');

await composer.click();
await page.keyboard.insertText(MESSAGE);

let send = await findSend(page);
if (send) await send.click();
else {
  const ai = await aiLocate(page);
  if (!ai?.send) throw new Error('Send button not found.');
  await page.mouse.click(ai.send.x, ai.send.y);
}

console.log('Message submitted.');
await page.waitForTimeout(Number(process.env.WAIT_MS || 1500));
await context.close();
