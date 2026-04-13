# Game Overlay

The game overlay is a transparent, always-on-top bar that shows your last 3 voice exchanges and current weather while you play. It sits over your game without blocking input.

---

## Showing and Hiding

| What to say | What happens |
|---|---|
| `show overlay` | Shows the overlay |
| `hide overlay` | Hides the overlay |

You can also assign a hotkey to toggle it — see **Hotkey** below.

---

## Weather on the Overlay

When the overlay is visible, saying "weather in \<city\>" pins the current conditions to the top of the overlay in real time:

- **Line 1:** City, temperature, and description
- **Line 2:** Today's high, low, and rain chance

> **Example:** "weather in Birmingham" → `Birmingham Alabama · 79°F · Sunny` / `H: 84°F  L: 53°F · Rain: 0%`

The weather stays pinned until you ask for a new city or restart VERA.

---

## Position

You can place the overlay in any corner or along the top/bottom edge of your screen.

1. Open the VERA UI
2. Go to **Settings** → **Game Overlay**
3. Select a position from the dropdown:
   - Top Left, Top Center, Top Right
   - Bottom Left, Bottom Center, Bottom Right
4. Click **Save**

The overlay repositions immediately if it is currently visible.

---

## Hotkey

Assign a key to toggle the overlay without using your voice:

1. Open the VERA UI
2. Go to **Settings** → **Game Overlay**
3. Click **Record** next to Overlay Hotkey
4. Press the key you want to use
5. Click **Save**

Press the key at any time to show or hide the overlay.

---

## Troubleshooting

**"The overlay isn't showing up"**
- Make sure you said "show overlay" or pressed your hotkey
- Check that the overlay position isn't off-screen (try changing it to Top Left)

**"The overlay is blocking my game"**
- The overlay is click-through — it should not intercept mouse or keyboard input
- If input is being blocked, try repositioning it to a corner of the screen

**"Weather isn't showing on the overlay"**
- Say "weather in \<city\>" while the overlay is visible — it only updates when you ask for weather
- Make sure you have an active internet connection
