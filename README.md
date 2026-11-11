# EVE Eyes 👀

**A small animated EVE-inspired face running on the M5Dial.**

EVE Eyes displays a pair of expressive eyes on the M5Dial's 240 × 240 LCD screen, inspired by EVE from *WALL·E*. The eyes can change emotions, blink, look around, react to touch and play short sound effects.

The project focuses on a clean, minimalist appearance: a pure black background and simple, solid-color shapes, with no gradients, glow effects or reflections.

## ✨ Features

- **8 facial expressions:** Calm, Happy, Love, Curious, Excited, Tired, Sad and Angry.
- **Automatic mode:** Expressions change randomly at regular intervals.
- **Manual mode:** Use the rotary encoder to switch between expressions.
- **Touch interaction:** Touching the screen makes the eyes grow larger temporarily.
- **Natural movements:** Random eye movements and occasional blinking.
- **16 selectable colors:** 8 soft pastel colors and 8 brighter colors.
- **Adjustable brightness:** Choose between 25%, 50%, 75% and 100%.
- **Automatic dimming:** Screen brightness decreases after 5 seconds without interaction.
- **Sound effects:** Short tones provide audio feedback for interactions and expressions.
- **Persistent settings:** Preferences are saved to the device's flash memory.

## 🖥️ Hardware

| Component | Description |
|---|---|
| Device | M5Stack M5Dial |
| Display | 240 × 240 pixel LCD |
| Input | Rotary encoder and push button |
| Touchscreen | Built-in touch interface |
| Audio | Built-in speaker |
| Storage | Internal flash memory |

## 🎮 Controls

### Normal screen

| Action | Function |
|---|---|
| Rotate the encoder | Change the facial expression |
| Short button press | Toggle AUTO / FIXED mode |
| Long button press | Open the settings menu |
| Tap the screen | Trigger the enlarged-eye reaction |
| Touch and hold | Open the settings menu |
| No interaction for 5 seconds | Dim the screen |
| Any new interaction | Restore screen brightness |

**Note:** Rotating the encoder automatically switches the device to FIXED mode so that your selected expression stays on screen.

### Settings menu

The menu provides access to the main configuration options:

| Setting | Available options |
|---|---|
| Mode | AUTO / FIXED |
| Color | 16 different colors |
| Brightness | 25%, 50%, 75%, 100% |
| Close | Return to the main screen |

You can navigate the menu using the rotary encoder and select an option with a short button press. You can also interact directly with the touchscreen.

## 😊 Expressions

EVE Eyes includes eight different facial expressions:

| Expression | Description |
|---|---|
| Calm | Two regular oval eyes |
| Happy | Closed eyes shaped like curved arches |
| Love | Heart-shaped eyes |
| Curious | One eye slightly larger than the other |
| Excited | Both eyes become larger |
| Tired | Lowered eyelids |
| Sad | Eyelids angled outward |
| Angry | Eyelids angled inward |

The expressions are drawn directly onto the LCD using simple geometric shapes.

## 🎨 Color palette

The project includes 16 selectable colors:

**Pastel colors**
- Aqua
- Butter yellow
- Pink
- Lavender
- Peach
- Periwinkle
- Sky blue
- Pastel coral

**Bright colors**
- Turquoise
- Yellow
- Bright pink
- Electric purple
- Orange
- Electric blue
- Green
- Coral red

The background always remains pure black.

## ⚙️ Installation

### Requirements

- An M5Stack M5Dial.
- Compatible M5 MicroPython firmware.
- Firmware providing the `M5`, `Widgets`, `Speaker` and `hardware.Rotary` APIs.

### Getting started

1. Flash compatible MicroPython firmware onto your M5Dial.
2. Connect the device to your computer.
3. Open your preferred M5 MicroPython development environment.
4. Copy the project script to the device.
5. Run the script.

The program initializes the display, rotary encoder, touchscreen and speaker when available.

## 💾 Settings storage

Your preferences are automatically saved in:

```text
/flash/eve_eyes.cfg
```

The configuration stores four values:

```text
mode color_index expression_index brightness_index
```

This means your selected mode, color, expression and brightness can be restored after restarting the device.

To restore the default settings, remove the configuration file from the device.

## 🔧 Technical details

- **Language:** MicroPython
- **Target device:** M5Stack M5Dial
- **Display resolution:** 240 × 240
- **Rendering:** Direct LCD drawing using geometric primitives.
- **Graphics:** No canvas or continuous animation rendering.
- **Refresh strategy:** The face is redrawn when its appearance changes.
- **Configuration:** Persistent local storage in `/flash`.

The display is intentionally not continuously redrawn. This keeps the rendering approach simple and avoids unnecessary updates when nothing changes.

## 📁 Project structure

```text
EVE-Eyes/
│
├── main.py
└── README.md
```

The main Python script contains the display rendering, expression logic, interaction handling, sound effects, menu system and configuration management.

## 🚀 Project

EVE Eyes is a small experiment in combining embedded programming, simple graphics and hardware interaction to create a friendly desktop companion.

Inspired by EVE from *WALL·E*.
