# VERA Terms of Service
Last updated: March 28, 2026

## 1. ACCEPTANCE OF TERMS
By downloading, installing, or using VERA ("the Software"), you agree to these Terms of Service. If you do not agree, do not use the Software.

## 2. ALPHA SOFTWARE DISCLAIMER
VERA is currently in alpha. It is provided for testing and early access purposes. Features may change, break, or be removed at any time without notice. Do not rely on VERA for critical tasks.

## 3. WHO CAN USE VERA
You must be at least 13 years old to use VERA. By using the Software, you confirm you meet this requirement.

## 4. DATA AND PRIVACY

### 4.1 Local Storage
VERA stores the following data locally on your machine only:
- `config.json` — your settings and preferences
- `memory.json` — conversational memory
- `transcripts.log` — a log of voice command transcripts
- `assistant.log` — a log of VERA actions

### 4.2 No Data Collection
Cope (the developer) does not collect, transmit, or have access to any of the above data. Your data stays on your machine.

### 4.3 Third Party Services
Certain optional features send data to third party services:
- **Gemini AI (Google)** — if you provide a Gemini API key, voice queries are sent to Google's servers under Google's Privacy Policy
- **Groq** — if you provide a Groq API key, voice queries are sent to Groq's servers under Groq's Privacy Policy
- **Discord** — if you configure Discord webhooks, messages are sent to Discord under Discord's Privacy Policy

You are responsible for reviewing the privacy policies of any third party services you choose to connect.

## 5. BUG REPORTS
When you submit a bug report through VERA, the following information is sent to a private Discord server operated by the developer:
- Your VERA version number
- Your description of the issue
- A zip file containing your `assistant.log`, `transcripts.log`, and `config.json`

`config.json` may contain API keys and webhook URLs you have entered. By submitting a bug report you consent to this data being shared with the developer for the purpose of diagnosing and fixing issues. This data will not be shared with third parties.

## 6. INTELLECTUAL PROPERTY
VERA and its source code are the property of the developer. You may not resell, redistribute, or claim ownership of the Software or any portion of it without explicit written permission.

## 7. NO WARRANTY
VERA IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT. THE DEVELOPER DOES NOT WARRANT THAT THE SOFTWARE WILL BE ERROR-FREE OR UNINTERRUPTED.

## 8. LIMITATION OF LIABILITY
TO THE FULLEST EXTENT PERMITTED BY LAW, THE DEVELOPER SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES ARISING FROM YOUR USE OF VERA, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. THE DEVELOPER'S TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT YOU PAID FOR THE SOFTWARE.

## 9. THIRD PARTY LICENSES
VERA uses the following open source libraries:
- pynput (LGPL-3.0)
- pystray (LGPL-3.0)
- faster-whisper (MIT)
- customtkinter (MIT)
- kokoro-onnx (Apache 2.0)

Source code is provided, satisfying the requirements of LGPL-3.0. Full license texts are available at their respective project pages.

## 10. CHANGES TO TERMS
The developer reserves the right to update these Terms at any time. Continued use of VERA after changes are posted constitutes acceptance of the new Terms.

## 11. GOVERNING LAW
These Terms are governed by the laws of the State of Alabama, United States, without regard to its conflict of law provisions.

## 12. CONTACT
For questions or concerns regarding these Terms, open a ticket in the VERA Support Discord.
