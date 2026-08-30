# Universal Message Agent

Agent scaffold for automating message entry and sending across apps.

## Intended flow

1. Detect the message input area using accessibility metadata and/or computer vision.
2. Focus the input.
3. Paste the configured message.
4. Detect the Send button (text/accessibility label/icon) near the input.
5. Click Send.
6. Verify that the message was submitted.

The implementation should prefer accessibility/UI semantics where available and use visual detection as a fallback. App-specific selectors should be configurable rather than hard-coded.
