import time
import math
import M5
from M5 import *
from hardware import Rotary

BUILD = "v7"

# ------------------------------------------------------------- palette
BG = 0x000000          # fond noir pur
CREAM = 0xFFFDF4
MUTED = 0x8E87A3
SOFT = 0xCFC7DE

# 8 pastels doux, puis 8 teintes plus vives
COLORS = (0x9FE7E0,    # aqua
          0xFFE3A3,    # beurre
          0xFFC2D1,    # rose
          0xC9B8F0,    # lavande
          0xFFCBA4,    # peche
          0xB9C6F2,    # pervenche
          0xA9D3F5,    # bleu ciel
          0xFFB3A7,    # corail pastel
          0x00E5D4,    # turquoise vive
          0xFFD000,    # jaune vif
          0xFF5C8A,    # rose vif
          0xA66BFF,    # violet electrique
          0xFF8A3D,    # orange vif
          0x4D7CFF,    # bleu electrique
          0x00C853,    # vert vif
          0xFF3B5C)    # rouge corail vif

EMO_TONE = (880, 1046, 1318, 1175, 1568, 523, 659, 740)

# ------------------------------------------------------- luminosite
BRIGHT_LEVELS = (64, 128, 191, 255)    # 25 / 50 / 75 / 100 %
BRIGHT_LABELS = ("25", "50", "75", "100")
DIM_LEVEL = 40                          # luminosite en veille
DIM_AFTER_MS = 5000                     # 5 s sans contact -> baisse

# ------------------------------------------------------------ geometrie
LX, RX = 78, 162       # centres des deux yeux
EY = 120
REG_X, REG_Y, REG_W, REG_H = 30, 72, 180, 96

GAZE_MIN_MS = 5000
GAZE_VAR_MS = 25000
GAZE_AMP = 12

# menu
M_TITLE_Y = 8
M_LAB_Y = 28
M_PILL_Y = 44
M_PILL_W = 48
M_PILL_H = 24
M_AUTO_X = 70
M_FIXE_X = 122
M_COL_LAB_Y = 76
M_SW_Y1 = 96
M_SW_Y2 = 118
M_SW_STEP = 24
M_SW_X0 = 36
M_LUM_LAB_Y = 132
BR_X0 = 50
BR_Y = 146
BR_W = 32
BR_H = 20
BR_GAP = 4
M_CLOSE_X = 84
M_CLOSE_Y = 172
M_CLOSE_W = 72
M_CLOSE_H = 22

AUTO_MIN_MS = 4200
AUTO_VAR_MS = 3200
SOUND_ON    = True
ROTARY_DIR  = 1
CFG_PATH    = "/flash/eve_eyes.cfg"

# ---------------------------------------------------------------- etat
idx = 0
mode = 0               # 0 = AUTO, 1 = FIXE
col_idx = 0
bright_idx = 3
dimmed = False
in_menu = False
focus = 0
face_dirty = True
was_blinking = False
was_poking = False

rot = None
spk_ok = False
has_btn = False
has_touch = False

next_auto = 0
next_blink = 0
blink_until = 0
poke_until = 0
next_sacc = 0
tx = 0
ty = 0
ox = 0
oy = 0
last_rot = 0
last_activity = 0
btn_guard = False
t_guard = False
menu_guard = 0
cfg_dirty = False
cfg_time = 0
seed = 0x2545F491


# ------------------------------------------------------------ utilitaires
def rnd(n):
    global seed
    seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (seed >> 8) % n


def play_tone(f, d):
    if SOUND_ON and spk_ok and not dimmed:
        try:
            Speaker.tone(f, d)
        except Exception:
            pass


def chirp(i):
    play_tone(EMO_TONE[i], 45)


def apply_brightness():
    try:
        Widgets.setBrightness(BRIGHT_LEVELS[bright_idx])
    except Exception:
        pass


def set_dim(on):
    global dimmed
    if on == dimmed:
        return
    dimmed = on
    try:
        if on:
            Widgets.setBrightness(DIM_LEVEL)
        else:
            Widgets.setBrightness(BRIGHT_LEVELS[bright_idx])
    except Exception:
        pass


def load_cfg():
    global mode, col_idx, idx, bright_idx
    try:
        f = open(CFG_PATH, "r")
        s = f.read()
        f.close()
        p = s.split()
        if len(p) >= 3:
            m = int(p[0])
            c = int(p[1])
            e = int(p[2])
            if m == 0 or m == 1:
                mode = m
            if c >= 0 and c < 16:
                col_idx = c
            if e >= 0 and e < 8:
                idx = e
        if len(p) >= 4:
            b = int(p[3])
            if b >= 0 and b < 4:
                bright_idx = b
    except Exception:
        pass


def save_cfg():
    try:
        f = open(CFG_PATH, "w")
        f.write(str(mode) + " " + str(col_idx) + " " +
                str(idx) + " " + str(bright_idx))
        f.close()
    except Exception:
        pass


# ------------------------------------------------------- dessin direct LCD
def c_rect(x, y, w, h, col):
    M5.Lcd.fillRect(x, y, w, h, col)


def c_circle(x, y, r, col):
    M5.Lcd.fillCircle(x, y, r, col)


def c_tri(x0, y0, x1, y1, x2, y2, col):
    M5.Lcd.fillTriangle(x0, y0, x1, y1, x2, y2, col)


# ------------------------------------------------------- formes des yeux
def eye_oval(cx, cy, rw, rh, col, lid_slope, lid_y):
    if rh < 1:
        return
    y = cy - rh
    while y <= cy + rh:
        v = (y - cy) / float(rh)
        if v < -1.0:
            v = -1.0
        elif v > 1.0:
            v = 1.0
        half = rw * math.sqrt(1.0 - v * v)
        xa = int(cx - half + 0.5)
        xb = int(cx + half + 0.5)
        if lid_slope == 0:
            if y < lid_y:
                y += 1
                continue
        elif lid_slope > 0:
            lim = cx + (y - lid_y) / lid_slope
            if xb > lim:
                xb = int(lim)
        else:
            lim = cx + (y - lid_y) / lid_slope
            if xa < lim:
                xa = int(lim) + 1
        if xb >= xa:
            c_rect(xa, y, xb - xa + 1, 1, col)
        y += 1


def eye_arc(cx, cy, rw, rh, th, col):
    x = cx - rw
    while x <= cx + rw:
        t = (x - cx) / float(rw)
        s = 1.0 - t * t
        if s < 0.0:
            s = 0.0
        y = int(cy - rh * math.sqrt(s))
        c_rect(x, y, 1, th, col)
        x += 1


def eye_heart(cx, cy, s, col):
    c_circle(cx - s // 2, cy - s // 3, s // 2, col)
    c_circle(cx + s // 2, cy - s // 3, s // 2, col)
    c_tri(cx - s, cy - s // 4, cx + s, cy - s // 4, cx, cy + s, col)


# --------------------------------------------------------------- visage
def draw_face(now):
    col = COLORS[col_idx]
    st = idx
    if time.ticks_diff(poke_until, now) > 0:
        st = 4

    M5.Lcd.startWrite()
    c_rect(REG_X, REG_Y, REG_W, REG_H, BG)

    if time.ticks_diff(blink_until, now) > 0 and st != 1:
        eye_oval(LX + ox, EY + oy, 32, 3, col, 0, 0)
        eye_oval(RX + ox, EY + oy, 32, 3, col, 0, 0)
        M5.Lcd.endWrite()
        return

    lx = LX + ox
    ex = RX + ox
    ly = EY + oy

    if st == 0:                       # CALME
        eye_oval(lx, ly, 32, 42, col, 0, 0)
        eye_oval(ex, ly, 32, 42, col, 0, 0)

    elif st == 1:                     # JOIE : yeux fermes en arche
        eye_arc(lx, ly - 8, 33, 21, 13, col)
        eye_arc(ex, ly - 8, 33, 21, 13, col)

    elif st == 2:                     # AMOUR : yeux en coeur
        eye_heart(lx, ly, 27, col)
        eye_heart(ex, ly, 27, col)

    elif st == 3:                     # CURIEUX : un oeil plus grand
        eye_oval(lx, ly + 2, 28, 36, col, 0, 0)
        eye_oval(ex, ly - 1, 34, 44, col, 0, 0)

    elif st == 4:                     # EXCITE / poke
        eye_oval(lx, ly, 34, 44, col, 0, 0)
        eye_oval(ex, ly, 34, 44, col, 0, 0)

    elif st == 5:                     # FATIGUE : paupiere basse
        eye_oval(lx, ly, 32, 42, col, 0, ly - 11)
        eye_oval(ex, ly, 32, 42, col, 0, ly - 11)

    elif st == 6:                     # TRISTE : paupiere vers l'exterieur
        eye_oval(lx, ly, 28, 40, col, -0.45, ly - 2)
        eye_oval(ex, ly, 28, 40, col, 0.45, ly - 2)

    else:                             # COLERE : paupiere vers l'interieur
        eye_oval(lx, ly, 32, 40, col, 0.45, ly - 5)
        eye_oval(ex, ly, 32, 40, col, -0.45, ly - 5)

    M5.Lcd.endWrite()


# ---------------------------------------------------------------- menu
def br_x(i):
    return BR_X0 + i * (BR_W + BR_GAP)


def draw_menu():
    L = M5.Lcd
    col = COLORS[col_idx]
    L.startWrite()
    L.fillScreen(BG)

    L.setFont(L.FONTS.Montserrat14)
    L.setTextColor(SOFT, BG)
    L.drawString("MENU", 102, M_TITLE_Y)

    L.setFont(L.FONTS.Montserrat12)
    L.setTextColor(MUTED, BG)
    L.drawString("MODE", 104, M_LAB_Y)

    if mode == 0:
        L.fillRoundRect(M_AUTO_X, M_PILL_Y, M_PILL_W, M_PILL_H, 12, col)
        L.setTextColor(BG, col)
    else:
        L.drawRoundRect(M_AUTO_X, M_PILL_Y, M_PILL_W, M_PILL_H, 12, MUTED)
        L.setTextColor(MUTED, BG)
    L.drawString("AUTO", M_AUTO_X + 8, M_PILL_Y + 6)

    if mode == 1:
        L.fillRoundRect(M_FIXE_X, M_PILL_Y, M_PILL_W, M_PILL_H, 12, col)
        L.setTextColor(BG, col)
    else:
        L.drawRoundRect(M_FIXE_X, M_PILL_Y, M_PILL_W, M_PILL_H, 12, MUTED)
        L.setTextColor(MUTED, BG)
    L.drawString("FIXE", M_FIXE_X + 8, M_PILL_Y + 6)

    L.setTextColor(MUTED, BG)
    L.drawString("COULEUR", 92, M_COL_LAB_Y)

    i = 0
    while i < 16:
        sy = M_SW_Y1
        if i >= 8:
            sy = M_SW_Y2
        x = M_SW_X0 + (i % 8) * M_SW_STEP
        L.fillCircle(x, sy, 6, COLORS[i])
        if i == col_idx:
            L.drawCircle(x, sy, 8, SOFT)
        if focus == 2 + i:
            L.drawCircle(x, sy, 10, CREAM)
        i += 1

    L.setTextColor(MUTED, BG)
    L.drawString("LUMIERE", 88, M_LUM_LAB_Y)

    i = 0
    while i < 4:
        x = br_x(i)
        if i == bright_idx:
            L.fillRoundRect(x, BR_Y, BR_W, BR_H, 9, col)
            L.setTextColor(BG, col)
        else:
            L.drawRoundRect(x, BR_Y, BR_W, BR_H, 9, MUTED)
            L.setTextColor(MUTED, BG)
        s = BRIGHT_LABELS[i]
        L.drawString(s, x + (BR_W - len(s) * 8) // 2, BR_Y + 5)
        i += 1

    L.drawRoundRect(M_CLOSE_X, M_CLOSE_Y, M_CLOSE_W, M_CLOSE_H, 11, MUTED)
    L.setTextColor(SOFT, BG)
    L.drawString("FERMER", M_CLOSE_X + 12, M_CLOSE_Y + 5)

    if focus == 0:
        L.drawRoundRect(M_AUTO_X - 3, M_PILL_Y - 3, M_PILL_W + 6,
                        M_PILL_H + 6, 15, CREAM)
    elif focus == 1:
        L.drawRoundRect(M_FIXE_X - 3, M_PILL_Y - 3, M_PILL_W + 6,
                        M_PILL_H + 6, 15, CREAM)
    elif focus >= 18 and focus <= 21:
        x = br_x(focus - 18)
        L.drawRoundRect(x - 3, BR_Y - 3, BR_W + 6, BR_H + 6, 11, CREAM)
    elif focus == 22:
        L.drawRoundRect(M_CLOSE_X - 3, M_CLOSE_Y - 3, M_CLOSE_W + 6,
                        M_CLOSE_H + 6, 13, CREAM)
    L.endWrite()


def menu_hit(x, y):
    if M_PILL_Y - 6 <= y <= M_PILL_Y + M_PILL_H + 6:
        if M_AUTO_X - 6 <= x <= M_AUTO_X + M_PILL_W + 6:
            return 0
        if M_FIXE_X - 6 <= x <= M_FIXE_X + M_PILL_W + 6:
            return 1
    row = -1
    if y >= M_SW_Y1 - 11 and y <= M_SW_Y1 + 11:
        row = 0
    elif y >= M_SW_Y2 - 11 and y <= M_SW_Y2 + 11:
        row = 1
    if row >= 0:
        i = 0
        while i < 8:
            sx = M_SW_X0 + i * M_SW_STEP
            if x >= sx - 11 and x <= sx + 11:
                return 2 + row * 8 + i
            i += 1
    if M_CLOSE_X - 6 <= x <= M_CLOSE_X + M_CLOSE_W + 6 and \
            M_CLOSE_Y - 6 <= y <= M_CLOSE_Y + M_CLOSE_H + 6:
        return 22
    if BR_Y - 7 <= y <= BR_Y + BR_H + 5:
        i = 0
        while i < 4:
            x0 = br_x(i)
            if x >= x0 - 5 and x <= x0 + BR_W + 5:
                return 18 + i
            i += 1
    return -1


def enter_menu():
    global in_menu, focus, menu_guard
    in_menu = True
    focus = mode
    menu_guard = time.ticks_ms() + 700
    draw_menu()
    play_tone(1318, 40)


def exit_menu():
    global in_menu, next_auto, cfg_dirty, menu_guard, face_dirty
    in_menu = False
    menu_guard = time.ticks_ms() + 700
    save_cfg()
    cfg_dirty = False
    if mode == 0:
        next_auto = time.ticks_ms() + 2500
    M5.Lcd.fillScreen(BG)
    face_dirty = True
    play_tone(880, 40)


def menu_activate(k):
    global mode, col_idx, bright_idx, focus, cfg_dirty, face_dirty
    if k == 0:
        mode = 0
        focus = 0
        cfg_dirty = True
        save_cfg()
        draw_menu()
        play_tone(1318, 40)
    elif k == 1:
        mode = 1
        focus = 1
        cfg_dirty = True
        save_cfg()
        draw_menu()
        play_tone(1175, 40)
    elif k >= 2 and k <= 17:
        col_idx = k - 2
        focus = k
        cfg_dirty = True
        face_dirty = True
        save_cfg()
        draw_menu()
        play_tone(1046, 40)
    elif k >= 18 and k <= 21:
        bright_idx = k - 18
        focus = k
        cfg_dirty = True
        apply_brightness()
        save_cfg()
        draw_menu()
        play_tone(988, 40)
    else:
        exit_menu()


# --------------------------------------------------------------- actions
def set_emotion(new, sound):
    global idx, face_dirty
    new = new % 8
    if new == idx:
        return
    idx = new
    face_dirty = True
    if sound:
        chirp(idx)


def set_mode(m):
    global mode, next_auto, cfg_dirty, cfg_time
    mode = m
    now = time.ticks_ms()
    if m == 0:
        next_auto = now + 2500
    cfg_dirty = True
    cfg_time = now


# ------------------------------------------------------------------ setup
def setup():
    global rot, spk_ok, has_btn, has_touch
    global next_auto, next_blink, next_sacc
    global ox, oy, tx, ty, blink_until, poke_until
    global last_rot, last_activity, btn_guard, t_guard, menu_guard
    global cfg_dirty, cfg_time, face_dirty, was_blinking, was_poking

    M5.begin()
    M5.Lcd.setRotation(0)
    try:
        Widgets.setBrightness(BRIGHT_LEVELS[3])
    except Exception:
        pass
    M5.Lcd.fillScreen(BG)

    load_cfg()
    apply_brightness()

    now = time.ticks_ms()
    ox = 0
    oy = 0
    tx = 0
    ty = 0
    blink_until = 0
    poke_until = 0
    was_blinking = False
    was_poking = False
    face_dirty = True
    draw_face(now)

    try:
        M5.Lcd.setFont(M5.Lcd.FONTS.Montserrat12)
        M5.Lcd.setTextColor(SOFT, BG)
        M5.Lcd.drawString(BUILD, 112, 18)
        time.sleep_ms(900)
        M5.Lcd.fillRect(100, 12, 40, 22, BG)
    except Exception:
        pass

    try:
        spk_ok = Speaker.begin()
    except Exception:
        spk_ok = False
    if spk_ok:
        try:
            Speaker.setVolume(40)
        except Exception:
            pass

    try:
        rot = Rotary()
    except Exception:
        rot = None
    try:
        has_btn = hasattr(M5.BtnA, "wasClicked")
    except Exception:
        has_btn = False
    try:
        has_touch = hasattr(M5, "Touch")
    except Exception:
        has_touch = False

    next_auto = now + 4500
    next_blink = now + 2600
    next_sacc = now + 4000
    last_rot = now
    last_activity = now
    btn_guard = False
    t_guard = False
    cfg_dirty = False
    cfg_time = now

    if SOUND_ON and spk_ok:
        try:
            Speaker.tone(660, 70)
            time.sleep_ms(55)
            Speaker.tone(880, 70)
            time.sleep_ms(55)
            Speaker.tone(1100, 90)
        except Exception:
            pass


# ------------------------------------------------------------------- loop
def loop():
    global next_auto, next_blink, blink_until, poke_until, next_sacc
    global tx, ty, ox, oy, last_rot, last_activity, focus, mode, idx
    global btn_guard, t_guard, menu_guard, cfg_dirty, cfg_time
    global face_dirty, was_blinking, was_poking

    M5.update()
    now = time.ticks_ms()

    # --- gestes bouton (lus chaque boucle : consomme les edges)
    btn_click = False
    btn_hold = False
    btn_press = False
    if has_btn:
        try:
            b_click = M5.BtnA.wasClicked()
            b_hold = M5.BtnA.wasHold()
            b_press = M5.BtnA.wasPressed()
            b_rel = M5.BtnA.wasReleased()
            if b_hold:
                btn_guard = True
            if btn_guard:
                b_click = False
            if b_rel or not M5.BtnA.isPressed():
                btn_guard = False
            btn_click = b_click
            btn_hold = b_hold
            btn_press = b_press
        except Exception:
            btn_guard = False

    # --- gestes tactiles
    t_click = False
    t_hold = False
    t_press = False
    t_x = 0
    t_y = 0
    if has_touch:
        try:
            d = M5.Touch.getDetail(0)
            t_click = d[6]
            t_hold = d[10]
            t_press = d[5]
            t_rel = d[8]
            t_pressed = d[4]
            if t_hold:
                t_guard = True
            if t_guard:
                t_click = False
            if t_rel or not t_pressed:
                t_guard = False
            t_x = M5.Touch.getX()
            t_y = M5.Touch.getY()
        except Exception:
            t_guard = False

    # --- rotation (lue une seule fois pour les deux ecrans)
    rot_event = False
    rot_step = 0
    if rot is not None:
        try:
            if rot.get_rotary_status():
                inc = rot.get_rotary_increments()
                if inc and time.ticks_diff(now, last_rot) > 70:
                    last_rot = now
                    rot_event = True
                    rot_step = 1 if (inc * ROTARY_DIR) > 0 else -1
        except Exception:
            pass

    # --- activite : reveille l'ecran
    if rot_event or btn_click or btn_hold or btn_press or \
            t_click or t_hold or t_press:
        last_activity = now
        if dimmed:
            set_dim(False)
            if t_press:
                t_guard = True

    # --- 5 s sans contact : baisse de luminosite
    if not dimmed and time.ticks_diff(now, last_activity) > DIM_AFTER_MS:
        set_dim(True)

    if dimmed:
        time.sleep_ms(40)
        return

    # ================================================= menu ouvert
    if in_menu:
        if rot_event:
            focus = (focus + rot_step) % 23
            draw_menu()

        if (btn_hold or t_hold) and \
                time.ticks_diff(now, menu_guard) >= 0:
            exit_menu()
        elif btn_click:
            menu_activate(focus)
        elif t_click:
            k = menu_hit(t_x, t_y)
            if k >= 0:
                menu_activate(k)

        time.sleep_ms(40)
        return

    # ================================================= ecran des yeux
    if rot_event:
        if mode == 0:
            mode = 1
            cfg_dirty = True
            cfg_time = now
        set_emotion(idx + rot_step, True)
        cfg_dirty = True
        cfg_time = now

    if (btn_hold or t_hold) and \
            time.ticks_diff(now, menu_guard) >= 0:
        enter_menu()
    elif btn_click:
        set_mode(0 if mode == 1 else 1)
        play_tone(988, 45)
    elif t_click:
        poke_until = now + 900
        play_tone(1568, 45)

    # defilement automatique (AUTO uniquement)
    if mode == 0 and time.ticks_diff(now, next_auto) >= 0:
        set_emotion(idx + 1 + rnd(7), True)
        next_auto = now + AUTO_MIN_MS + rnd(AUTO_VAR_MS)

    # clignements
    if time.ticks_diff(now, next_blink) >= 0:
        blink_until = now + 150
        next_blink = now + 2400 + rnd(3200)

    blinking = time.ticks_diff(blink_until, now) > 0
    if blinking != was_blinking:
        was_blinking = blinking
        face_dirty = True
    poking = time.ticks_diff(poke_until, now) > 0
    if poking != was_poking:
        was_poking = poking
        face_dirty = True

    # regard : nouvelle direction toutes les 5 a 30 s
    if time.ticks_diff(now, next_sacc) >= 0:
        sel = rnd(5)
        if sel == 0:
            tx = -GAZE_AMP
        elif sel == 1:
            tx = -(GAZE_AMP // 2)
        elif sel == 2:
            tx = 0
        elif sel == 3:
            tx = GAZE_AMP // 2
        else:
            tx = GAZE_AMP
        ty = (rnd(3) - 1) * 3
        next_sacc = now + GAZE_MIN_MS + rnd(GAZE_VAR_MS)
    moved = False
    if ox < tx:
        ox += 1
        moved = True
    elif ox > tx:
        ox -= 1
        moved = True
    if oy < ty:
        oy += 1
        moved = True
    elif oy > ty:
        oy -= 1
        moved = True
    if moved:
        face_dirty = True

    if cfg_dirty and time.ticks_diff(now, cfg_time) > 1500:
        save_cfg()
        cfg_dirty = False

    if face_dirty:
        draw_face(now)
        face_dirty = False

    time.sleep_ms(40)


if __name__ == "__main__":
    try:
        setup()
        while True:
            loop()
    except (Exception, KeyboardInterrupt) as e:
        try:
            from utility import print_error_msg

            print_error_msg(e)
        except ImportError:
            print("please update to latest firmware")
