# ChatGPT VPS UI Agent

AI-assisted browser agent for `https://chatgpt.com/`.

## VPS setup

```bash
cd agent
npm install
npx playwright install --with-deps chromium
export OPENAI_API_KEY='...'
export MESSAGE='Tin nhắn cần gửi'
npm start
```

The browser should have an authenticated session. Do not put passwords, cookies, session tokens, or API keys in the repository. The agent uses normal UI interaction: locate the message composer, insert the configured message, then locate and click Send. AI vision is only used as a fallback when normal accessibility/DOM locators cannot find a target.

For unattended use, provide a persistent browser profile on the VPS and set `CHATGPT_PROFILE` to that directory. Complete login manually once; do not automate CAPTCHA or authentication challenges.
