import sys
import math
import json
import os
import time
import pygame

# ==================================================
# INITIALIZATION
# ==================================================

try:
    import pygame
except ImportError:
    print("Install Pygame using: py -3.13 -m pip install pygame")
    input("Press Enter to exit...")
    sys.exit(1)

pygame.init()

MUSIC_ENABLED = True

try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except pygame.error as error:
    print("Music initialization failed:", error)
    MUSIC_ENABLED = False

display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("PC Builder Simulator")

WIDTH, HEIGHT = 1000, 650
screen = pygame.Surface((WIDTH, HEIGHT))
clock = pygame.time.Clock()

BG = (10, 16, 29)
PANEL = (22, 32, 51)
PANEL_HOVER = (35, 51, 77)
BLUE = (0, 135, 255)
BLUE_LIGHT = (55, 175, 255)
WHITE = (240, 245, 255)
MUTED = (155, 173, 199)
GREEN = (65, 215, 150)
RED = (255, 90, 105)
PURPLE = (160, 105, 255)
BORDER = (54, 73, 106)

font = pygame.font.SysFont("segoeui", 18)
small_font = pygame.font.SysFont("segoeui", 14)
medium_font = pygame.font.SysFont("segoeui", 26, bold=True)
big_font = pygame.font.SysFont("segoeui", 45, bold=True)

state = "menu"
running = True
buttons = []

budget = 800
money = budget
message = ""
message_timer = 0
category_index = 0
shop_page = 0
dragging_volume = False
income_timer = 0

# Offline earnings popup information
offline_popup_active = False
offline_earnings_notice = None

# ==================================================
# OFFLINE INCOME SETTINGS
# ==================================================

MAX_OFFLINE_SECONDS = 24 * 60 * 60

# ==================================================
# FILE LOCATIONS
# ==================================================

GAME_FOLDER = os.path.dirname(os.path.abspath(sys.argv[0]))

SAVE_FILE = os.path.join(GAME_FOLDER, "savegame.json")
SETTINGS_FILE = os.path.join(GAME_FOLDER, "settings.json")

MENU_MUSIC = os.path.join(GAME_FOLDER, "menu_music.mp3")
BUILD_MUSIC = os.path.join(GAME_FOLDER, "build_music.mp3")

# ==================================================
# AUDIO SETTINGS
# ==================================================

music_volume = 0.25
music_muted = False
current_music = None


def load_settings():
    global music_volume, music_muted

    if not os.path.exists(SETTINGS_FILE):
        return

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        music_volume = max(
            0.0, min(1.0, float(data.get("music_volume", 0.25)))
        )
        music_muted = bool(data.get("music_muted", False))

    except (OSError, ValueError, TypeError):
        pass


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump({
                "music_volume": music_volume,
                "music_muted": music_muted
            }, file, indent=4)
    except OSError as error:
        print("Could not save settings:", error)


def update_music_volume():
    if MUSIC_ENABLED and pygame.mixer.get_init():
        pygame.mixer.music.set_volume(
            0.0 if music_muted else music_volume
        )


def play_music(music_file):
    global current_music

    if not MUSIC_ENABLED:
        return

    if current_music != music_file:
        if not os.path.exists(music_file):
            return

        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
            current_music = music_file
        except pygame.error:
            current_music = None
            return

    update_music_volume()


# ==================================================
# PARTS SHOP
# ==================================================

parts = {
    "CPU": [
        ("Ryzen 5 3600", 90),
        ("Ryzen 5 5600", 400),
        ("Ryzen 7 5800X", 1500),
        ("Ryzen 7 7800X3D", 3500),
        ("Ryzen 9 7900X", 6000),
        ("Ryzen 9 9950X", 12000),
        ("Intel Core Ultra 9", 25000),
        ("Ryzen 9 Extreme Edition", 60000),
        ("QuantumCore X1", 200000),
        ("QuantumCore X1 Ultimate", 350000),
    ],
    "GPU": [
        ("GTX 1660 Super", 120),
        ("RTX 3060", 350),
        ("RTX 4060", 900),
        ("RTX 4070 Super", 2500),
        ("RTX 5070", 6000),
        ("RTX 5080", 18000),
        ("RTX 5090", 34000),
        ("Titan Ultra", 90000),
        ("Titan Ultra X", 250000),
        ("Quantum GPU X", 750000),
    ],
    "RAM": [
        ("8GB DDR4", 25),
        ("16GB DDR4", 300),
        ("32GB DDR4", 1100),
        ("32GB DDR5", 4000),
        ("64GB DDR5", 12000),
        ("96GB DDR5", 22000),
        ("128GB DDR5", 47000),
        ("192GB DDR5", 100000),
        ("512GB Workstation RAM", 250000),
        ("1TB Quantum Memory", 1000000),
    ],
    "Storage": [
        ("256GB SATA SSD", 25),
        ("500GB SSD", 500),
        ("1TB NVMe SSD", 4200),
        ("2TB NVMe SSD", 9000),
        ("4TB NVMe SSD", 16000),
        ("8TB NVMe SSD", 27000),
        ("16TB Enterprise SSD", 48000),
        ("30TB Professional SSD", 120000),
        ("100TB Storage Array", 300000),
        ("1PB Quantum Storage", 800000),
    ],
    "Motherboard": [
        ("Basic A320 Board", 40),
        ("B450 Motherboard", 600),
        ("B550 Motherboard", 3000),
        ("X570 Motherboard", 8000),
        ("B650 Motherboard", 17000),
        ("X870 Motherboard", 31000),
        ("Creator Workstation Board", 70000),
        ("Extreme Overclocking Board", 150000),
        ("Dual CPU Server Board", 350000),
        ("Quantum Computing Board", 600000),
    ],
    "Power Supply": [
        ("450W Bronze PSU", 35),
        ("550W Bronze PSU", 500),
        ("650W Gold PSU", 3400),
        ("750W Gold PSU", 7500),
        ("850W Platinum PSU", 15000),
        ("1000W Platinum PSU", 36000),
        ("1200W Titanium PSU", 70000),
        ("1600W Professional PSU", 120000),
        ("2000W Server Power Unit", 260000),
        ("Quantum Power Generator", 550000),
    ],
    "Case": [
        ("Basic Office Case", 30),
        ("Compact Case", 400),
        ("Mid Tower Case", 2500),
        ("Airflow RGB Case", 6000),
        ("Premium Glass Case", 15000),
        ("Full Tower Case", 35000),
        ("Dual Chamber Showcase", 75000),
        ("Professional Showpiece", 150000),
        ("Custom Liquid Cooling Tower", 280000),
        ("Quantum Glass Chassis", 620000),
    ],
}

categories = list(parts.keys())
SHOP_ITEMS_PER_PAGE = 4

selected = {}
inventory = []
inventory_capacity = 3
inventory_scroll = 0
total_sold = 0
total_earned = 0

# ==================================================
# SAVE AND LOAD GAME
# ==================================================

def save_game():
    data = {
        "money": money,
        "selected": selected,
        "inventory": inventory,
        "inventory_capacity": inventory_capacity,
        "total_sold": total_sold,
        "total_earned": total_earned,
        "category_index": category_index,
        "inventory_scroll": inventory_scroll,
        "last_saved_time": time.time(),
    }

    temporary_file = SAVE_FILE + ".tmp"

    try:
        with open(temporary_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        os.replace(temporary_file, SAVE_FILE)

    except (OSError, TypeError, ValueError) as error:
        print("Could not save game:", error)

        try:
            if os.path.exists(temporary_file):
                os.remove(temporary_file)
        except OSError:
            pass


def load_game():
    global money, selected, inventory
    global inventory_capacity, total_sold, total_earned
    global category_index, inventory_scroll
    global offline_popup_active, offline_earnings_notice

    if not os.path.exists(SAVE_FILE):
        return

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid save format")

        loaded_money = max(0, int(data.get("money", budget)))
        loaded_selected = {}
        saved_selected = data.get("selected", {})

        if isinstance(saved_selected, dict):
            for category, item in saved_selected.items():
                if category not in categories:
                    continue

                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    continue

                name, price = item

                if not isinstance(name, str):
                    continue

                try:
                    price = int(price)
                except (TypeError, ValueError):
                    continue

                if price >= 0:
                    loaded_selected[category] = (name, price)

        loaded_inventory = []

        for pc in data.get("inventory", []):
            if not isinstance(pc, dict):
                continue

            loaded_pc = {}
            valid = True

            for category in categories:
                item = pc.get(category)

                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    valid = False
                    break

                name, price = item

                if not isinstance(name, str):
                    valid = False
                    break

                try:
                    price = int(price)
                except (TypeError, ValueError):
                    valid = False
                    break

                if price < 0:
                    valid = False
                    break

                loaded_pc[category] = (name, price)

            if valid:
                loaded_inventory.append(loaded_pc)

        loaded_capacity = max(
            3, min(15, int(data.get("inventory_capacity", 3)))
        )
        loaded_capacity = max(loaded_capacity, len(loaded_inventory))

        money = loaded_money
        selected = loaded_selected
        inventory = loaded_inventory
        inventory_capacity = loaded_capacity

        total_sold = max(0, int(data.get("total_sold", 0)))
        total_earned = max(0, int(data.get("total_earned", 0)))

        category_index = max(
            0,
            min(
                len(categories) - 1,
                int(data.get("category_index", 0))
            )
        )

        inventory_scroll = max(
            0,
            min(
                int(data.get("inventory_scroll", 0)),
                max(0, len(inventory) - 6)
            )
        )

        # Calculate offline earnings.
        try:
            last_saved_time = float(
                data.get("last_saved_time", time.time())
            )
        except (TypeError, ValueError):
            last_saved_time = time.time()

        current_time = time.time()

        offline_seconds = max(
            0,
            min(
                current_time - last_saved_time,
                MAX_OFFLINE_SECONDS
            )
        )

        income_per_second = sum(
            passive_income(pc) for pc in inventory
        )

        offline_earnings = int(
            income_per_second * offline_seconds
        )

        # Store the popup details and apply earnings once.
        if offline_earnings > 0:
            money += offline_earnings
            total_earned += offline_earnings

            offline_earnings_notice = {
                "earnings": offline_earnings,
                "seconds": int(offline_seconds),
                "rate": income_per_second,
            }
            offline_popup_active = True

        # Save immediately so this offline period cannot be paid twice.
        save_game()

    except (OSError, ValueError, TypeError, KeyError) as error:
        print("Could not load save:", error)


# ==================================================
# DRAWING HELPERS
# ==================================================

def mouse_pos():
    mx, my = pygame.mouse.get_pos()
    dw, dh = display.get_size()
    return int(mx * WIDTH / dw), int(my * HEIGHT / dh)


def event_position(pos):
    return (
        int(pos[0] * WIDTH / display.get_width()),
        int(pos[1] * HEIGHT / display.get_height())
    )


def draw_text(label, x, y, color=WHITE, f=font, center=False):
    image = f.render(str(label), True, color)
    rect = image.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(image, rect)


def draw_panel(rect, color=PANEL, outline=BORDER, radius=12):
    pygame.draw.rect(screen, color, rect, border_radius=radius)

    if outline:
        pygame.draw.rect(
            screen, outline, rect, 1, border_radius=radius
        )


def add_button(label, rect, action, color=PANEL, f=small_font):
    rect = pygame.Rect(rect)
    hovered = rect.collidepoint(mouse_pos())

    pygame.draw.rect(
        screen,
        PANEL_HOVER if hovered else color,
        rect,
        border_radius=9
    )
    pygame.draw.rect(
        screen,
        BLUE_LIGHT if hovered else BORDER,
        rect,
        1,
        border_radius=9
    )

    draw_text(label, rect.centerx, rect.centery, WHITE, f, True)
    buttons.append((rect, action))


def draw_background():
    screen.fill(BG)

    pygame.draw.circle(screen, (18, 35, 65), (820, 180), 230)
    pygame.draw.circle(screen, (15, 27, 48), (100, 520), 240)

    for x in range(0, WIDTH, 40):
        pygame.draw.line(
            screen, (17, 25, 40), (x, 0), (x, HEIGHT)
        )

    pygame.draw.line(screen, BLUE, (0, 185), (185, 0), 3)
    pygame.draw.line(screen, BLUE, (0, 510), (140, 650), 2)

    pygame.draw.rect(screen, (12, 17, 28), (0, 590, WIDTH, 60))
    pygame.draw.line(
        screen, (36, 49, 70), (0, 590), (WIDTH, 590), 2
    )


def notify(text):
    global message, message_timer
    message = text
    message_timer = 180


def total_spent(build=None):
    if build is None:
        build = selected
    return sum(item[1] for item in build.values())


def is_complete(build=None):
    if build is None:
        build = selected
    return all(category in build for category in categories)


def sale_value(build):
    return round(total_spent(build) * 1.20)


def format_duration(seconds):
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60

    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {remaining_seconds}s"
    return f"{remaining_seconds}s"


# ==================================================
# PASSIVE INCOME
# ==================================================

def passive_income(build):
    if not is_complete(build):
        return 0

    income_rates = {
        "CPU": 0.010,
        "GPU": 0.020,
        "RAM": 0.005,
        "Storage": 0.005,
        "Motherboard": 0.005,
        "Power Supply": 0.003,
        "Case": 0.003,
    }

    income = 0.0

    for category in categories:
        if category not in build:
            continue

        item = build[category]

        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue

        try:
            price = max(0, int(item[1]))
        except (TypeError, ValueError):
            continue

        rate = income_rates.get(category, 0.005)
        income += price * rate

    return max(5, round(income))


def reset_build():
    global selected, message, message_timer, category_index, shop_page

    selected = {}
    message = ""
    message_timer = 0
    category_index = 0
    shop_page = 0


def start_new_game():
    global money, inventory, inventory_capacity
    global total_sold, total_earned, income_timer, inventory_scroll

    money = budget
    inventory = []
    inventory_capacity = 3
    total_sold = 0
    total_earned = 0
    income_timer = 0
    inventory_scroll = 0

    reset_build()
    save_game()


# ==================================================
# TYCOON FEATURES
# ==================================================

def sell_current_pc():
    global money, total_sold, total_earned, state

    if not is_complete():
        notify("Install every part before selling your PC!")
        return

    price = sale_value(selected)
    profit = price - total_spent()

    money += price
    total_earned += profit
    total_sold += 1

    reset_build()
    state = "floor"

    save_game()
    notify(f"PC sold for ${price:,}! Profit: ${profit:,}")


def store_current_pc():
    global state

    if not is_complete():
        notify("Install every part before storing your PC!")
        return

    if len(inventory) >= inventory_capacity:
        notify("Inventory full! Upgrade your inventory first.")
        return

    inventory.append(dict(selected))

    reset_build()
    state = "floor"

    save_game()
    notify("PC stored! It now earns passive income.")


def sell_inventory_pc(index):
    global money, total_sold, total_earned, state, inventory_scroll

    if not 0 <= index < len(inventory):
        return

    pc = inventory.pop(index)
    price = sale_value(pc)
    profit = price - total_spent(pc)

    money += price
    total_earned += profit
    total_sold += 1

    inventory_scroll = min(
        inventory_scroll,
        max(0, len(inventory) - 6)
    )

    state = "inventory"

    save_game()
    notify(f"Stored PC sold! Profit: ${profit:,}")


def upgrade_inventory():
    global money, inventory_capacity

    if inventory_capacity >= 15:
        notify("Inventory capacity is maxed!")
        return

    upgrade_cost = 2500 * (inventory_capacity - 2)

    if money < upgrade_cost:
        notify(f"You need ${upgrade_cost:,} for this upgrade.")
        return

    money -= upgrade_cost
    inventory_capacity = min(15, inventory_capacity + 2)

    save_game()
    notify(f"Inventory upgraded to {inventory_capacity} slots!")


# ==================================================
# DECORATIVE PC
# ==================================================

def draw_pc():
    pygame.draw.rect(screen, (17, 22, 34), (720, 490, 280, 100))
    pygame.draw.line(
        screen, (35, 52, 78), (720, 490), (1000, 490), 3
    )

    draw_panel((770, 235, 180, 265), (9, 14, 24), (39, 63, 101), 13)
    draw_panel((782, 248, 132, 236), (15, 28, 46), (30, 62, 100), 8)

    pygame.draw.rect(
        screen, (25, 52, 51), (794, 263, 108, 204), border_radius=5
    )

    pygame.draw.circle(screen, (0, 50, 90), (835, 305), 32)
    pygame.draw.circle(screen, BLUE, (835, 305), 27, 3)
    pygame.draw.circle(screen, BLUE_LIGHT, (835, 305), 13, 2)
    pygame.draw.circle(screen, WHITE, (835, 305), 5)

    for angle in range(0, 360, 60):
        a = math.radians(angle)
        x1 = int(835 + math.cos(a) * 13)
        y1 = int(305 + math.sin(a) * 13)
        x2 = int(835 + math.cos(a + 0.5) * 23)
        y2 = int(305 + math.sin(a + 0.5) * 23)
        pygame.draw.line(screen, BLUE_LIGHT, (x1, y1), (x2, y2), 3)

    for x in (876, 889):
        pygame.draw.rect(
            screen, PURPLE, (x, 267, 7, 68), border_radius=2
        )

    draw_panel((794, 365, 108, 45), (30, 42, 61), BLUE, 5)

    for x in (817, 855):
        pygame.draw.circle(screen, BLUE_LIGHT, (x, 387), 13, 2)
        pygame.draw.circle(screen, BLUE, (x, 387), 5)

    pygame.draw.rect(
        screen, (23, 29, 41), (794, 428, 108, 35), border_radius=4
    )
    pygame.draw.line(screen, BLUE, (774, 257), (774, 475), 3)
    pygame.draw.line(screen, BLUE, (920, 260), (920, 480), 2)

    draw_text("PC SYSTEM", 860, 520, MUTED, small_font, True)


# ==================================================
# MAIN MENU
# ==================================================

def draw_menu():
    draw_background()

    # Main-menu money display in the top-right corner.
    draw_panel((790, 12, 195, 58), (19, 29, 47), BLUE, 10)
    draw_text("YOUR MONEY", 805, 20, MUTED, small_font)
    draw_text(f"${money:,}", 805, 39, GREEN, medium_font)

    help_rect = pygame.Rect(10, 10, 44, 44)
    hovered = help_rect.collidepoint(mouse_pos())

    pygame.draw.circle(
        screen, BLUE_LIGHT if hovered else BLUE,
        help_rect.center, 20, 2
    )
    draw_text("?", 32, 31, WHITE, medium_font, True)
    buttons.append((help_rect, "help"))

    gear_rect = pygame.Rect(65, 10, 44, 44)
    gear_hovered = gear_rect.collidepoint(mouse_pos())

    pygame.draw.circle(
        screen, BLUE_LIGHT if gear_hovered else BLUE,
        gear_rect.center, 20, 2
    )

    gx, gy = gear_rect.center
    pygame.draw.circle(screen, WHITE, (gx, gy), 8, 3)
    pygame.draw.circle(screen, WHITE, (gx, gy), 3)

    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        x1 = int(gx + math.cos(radians) * 11)
        y1 = int(gy + math.sin(radians) * 11)
        x2 = int(gx + math.cos(radians) * 15)
        y2 = int(gy + math.sin(radians) * 15)
        pygame.draw.line(screen, WHITE, (x1, y1), (x2, y2), 3)

    buttons.append((gear_rect, "settings"))

    draw_text("WELCOME TO", 350, 105, BLUE_LIGHT, small_font, True)
    draw_text("PC BUILDER", 350, 157, WHITE, big_font, True)
    draw_text("S I M U L A T O R", 350, 207, BLUE, medium_font, True)

    pygame.draw.line(screen, BLUE, (190, 235), (510, 235), 3)

    draw_text("Build your dream computer.", 350, 266, MUTED, font, True)

    add_button(
        "START BUILDING", (190, 320, 320, 58),
        "start", BLUE, medium_font
    )
    add_button(
        "QUIT GAME", (230, 398, 240, 48),
        "quit", PANEL, font
    )

    draw_pc()
    draw_text("BUILD  •  LEARN  •  UPGRADE", 820, 570, MUTED, small_font, True)


# ==================================================
# OFFLINE EARNINGS POPUP
# ==================================================

def draw_offline_popup():
    if not offline_popup_active or not offline_earnings_notice:
        return

    # Dark overlay over the menu.
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    # Popup panel.
    popup_rect = pygame.Rect(250, 175, 500, 300)
    draw_panel(popup_rect, (19, 29, 47), BLUE, 18)

    draw_text(
        "WELCOME BACK!",
        500, 215, BLUE_LIGHT, big_font, True
    )

    draw_text(
        "Your stored PCs kept earning while you were away.",
        500, 260, MUTED, small_font, True
    )

    earnings = offline_earnings_notice["earnings"]
    seconds = offline_earnings_notice["seconds"]
    rate = offline_earnings_notice["rate"]

    draw_text(
        f"Time away: {format_duration(seconds)}",
        500, 305, WHITE, font, True
    )

    draw_text(
        f"Income rate: ${rate:,} per second",
        500, 337, MUTED, small_font, True
    )

    draw_text(
        f"+${earnings:,}",
        500, 385, GREEN, big_font, True
    )

    draw_text(
        "OFFLINE EARNINGS",
        500, 420, MUTED, small_font, True
    )

    add_button(
        "CONTINUE",
        (375, 435, 250, 45),
        "close_offline_popup",
        BLUE,
        font
    )


# ==================================================
# HELP MENU
# ==================================================

def draw_help():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))

    draw_panel((230, 150, 540, 350), (19, 29, 47), BLUE, 16)

    draw_text("HELP & TIPS", 500, 200, WHITE, medium_font, True)
    pygame.draw.line(screen, BLUE, (300, 232), (700, 232), 2)

    draw_text(
        "Browse the shop to choose your PC parts.",
        500, 285, WHITE, font, True
    )
    draw_text(
        "Buy better parts as you earn more money.",
        500, 325, MUTED, small_font, True
    )
    draw_text(
        "Sell PCs for profit or store them for passive income.",
        500, 360, MUTED, small_font, True
    )
    draw_text(
        "Use the shop pages to browse every part.",
        500, 390, MUTED, small_font, True
    )

    add_button("BACK TO MENU", (380, 435, 240, 48), "back", PANEL, font)


# ==================================================
# SETTINGS MENU
# ==================================================

def draw_settings():
    draw_background()

    draw_text("SETTINGS", 500, 100, BLUE_LIGHT, big_font, True)
    draw_text("Customize your game experience", 500, 145, MUTED, font, True)

    draw_panel((220, 185, 560, 300), (19, 29, 47), BLUE, 16)
    draw_text("MUSIC VOLUME", 270, 225, WHITE, medium_font)

    draw_text(f"{round(music_volume * 100)}%", 730, 230, GREEN, font, True)

    slider_rect = pygame.Rect(270, 275, 460, 12)
    pygame.draw.rect(screen, (40, 52, 72), slider_rect, border_radius=6)

    filled_width = int(slider_rect.width * music_volume)

    if filled_width > 0:
        pygame.draw.rect(
            screen, BLUE,
            (slider_rect.x, slider_rect.y, filled_width, slider_rect.height),
            border_radius=6
        )

    handle_x = slider_rect.x + filled_width
    pygame.draw.circle(screen, WHITE, (handle_x, slider_rect.centery), 11)
    pygame.draw.circle(screen, BLUE, (handle_x, slider_rect.centery), 6)

    buttons.append((pygame.Rect(255, 255, 490, 45), "volume_slider"))

    mute_label = "UNMUTE MUSIC" if music_muted else "MUTE MUSIC"
    mute_color = (130, 45, 60) if music_muted else PANEL

    add_button(
        mute_label, (350, 330, 300, 48),
        "toggle_mute", mute_color, font
    )

    draw_text(
        "Volume settings are saved automatically.",
        500, 405, MUTED, small_font, True
    )

    add_button(
        "BACK TO MENU", (370, 515, 260, 48),
        "settings_back", BLUE, font
    )


# ==================================================
# BUILD FLOOR
# ==================================================

def draw_pc_small():
    draw_panel((770, 220, 165, 270), (9, 14, 24), (39, 63, 101), 13)
    draw_panel((782, 233, 141, 244), (15, 28, 46), (30, 62, 100), 8)

    pygame.draw.rect(
        screen, (25, 52, 51), (795, 249, 115, 210), border_radius=5
    )

    pygame.draw.circle(screen, (0, 50, 90), (852, 292), 30)
    pygame.draw.circle(screen, BLUE, (852, 292), 25, 3)
    pygame.draw.circle(screen, BLUE_LIGHT, (852, 292), 12, 2)

    for x in (884, 895):
        pygame.draw.rect(screen, PURPLE, (x, 260, 6, 65), border_radius=2)

    draw_panel((802, 350, 102, 42), (30, 42, 61), BLUE, 5)

    for x in (825, 865):
        pygame.draw.circle(screen, BLUE_LIGHT, (x, 371), 11, 2)

    pygame.draw.rect(
        screen, (23, 29, 41), (802, 410, 102, 35), border_radius=4
    )
    draw_text("YOUR PC", 852, 510, MUTED, small_font, True)


def draw_header(title, subtitle):
    draw_text(title, 30, 18, BLUE_LIGHT, small_font)
    draw_text(subtitle, 30, 43, WHITE, medium_font)

    draw_panel((670, 18, 290, 62))
    draw_text("WALLET", 690, 27, MUTED, small_font)
    draw_text(f"${money:,}", 690, 45, GREEN, medium_font)
    draw_text(f"Spent: ${total_spent():,}", 835, 48, WHITE, small_font)


def draw_floor():
    draw_background()
    draw_header("BUILD FLOOR", "Your PC workshop")

    draw_panel((30, 120, 610, 390))
    draw_text("WORKBENCH", 55, 142, BLUE_LIGHT, medium_font)
    draw_text(
        "Choose parts in the shop, then return here to review your build.",
        55, 183, MUTED, small_font
    )

    draw_panel((55, 225, 560, 230), (15, 25, 41), BORDER, 10)

    if not selected:
        draw_text("No parts purchased yet", 335, 330, MUTED, font, True)
        draw_text(
            "Open the shop to start building your PC.",
            335, 362, MUTED, small_font, True
        )
    else:
        y = 245

        for category in categories:
            if category in selected:
                name, price = selected[category]
                draw_text(category, 75, y, BLUE_LIGHT, small_font)
                draw_text(name, 220, y, WHITE, small_font)
                draw_text(f"${price:,}", 565, y, GREEN, small_font)
                y += 31

    draw_pc_small()

    add_button("OPEN PARTS SHOP", (55, 530, 220, 48), "shop", BLUE, font)
    add_button("FINISH BUILD", (290, 530, 170, 48), "finish", (30, 100, 75), font)
    add_button("MAIN MENU", (480, 530, 150, 48), "menu", PANEL, font)

    draw_text(
        f"Inventory: {len(inventory)}/{inventory_capacity}",
        805, 550, MUTED, small_font, True
    )

    income = sum(passive_income(pc) for pc in inventory)
    draw_text(f"Income: ${income}/sec", 805, 573, GREEN, small_font, True)

    if message_timer > 0:
        draw_panel((660, 535, 300, 36), PANEL_HOVER)
        draw_text(message, 810, 553, WHITE, small_font, True)

    add_button("INVENTORY", (665, 610, 140, 30), "inventory", PANEL, small_font)


# ==================================================
# PARTS SHOP
# ==================================================

def draw_shop():
    draw_background()

    category = categories[category_index]
    item_list = parts[category]
    total_pages = math.ceil(len(item_list) / SHOP_ITEMS_PER_PAGE)

    draw_header("PARTS SHOP", f"Shop / {category}")
    draw_text("Choose a category", 30, 105, MUTED, small_font)

    for i, cat in enumerate(categories):
        row = i // 4
        col = i % 4
        x = 30 + col * 138
        y = 128 + row * 43

        add_button(
            cat, (x, y, 128, 34), ("category", i),
            BLUE if i == category_index else PANEL, small_font
        )

    draw_panel((30, 225, 680, 310))
    draw_text(f"{category.upper()} OPTIONS", 55, 242, BLUE_LIGHT, medium_font)
    draw_text(
        f"Page {shop_page + 1}/{total_pages} | {len(item_list)} parts",
        570, 251, MUTED, small_font, True
    )
    draw_text("Click BUY to purchase a component.", 55, 278, MUTED, small_font)

    start_index = shop_page * SHOP_ITEMS_PER_PAGE
    end_index = min(start_index + SHOP_ITEMS_PER_PAGE, len(item_list))

    for i in range(start_index, end_index):
        name, price = item_list[i]
        row = i - start_index
        y = 305 + row * 43
        is_owned = selected.get(category) == (name, price)

        draw_panel(
            (50, y, 635, 37),
            (25, 67, 58) if is_owned else (17, 27, 44),
            GREEN if is_owned else BORDER, 7
        )

        draw_text(name, 65, y + 9, WHITE, small_font)
        draw_text(f"${price:,}", 420, y + 9, GREEN, font)

        add_button(
            "OWNED" if is_owned else "BUY",
            (535, y + 4, 130, 29),
            ("buy", category, (name, price)),
            (30, 90, 72) if is_owned else BLUE
        )

    if shop_page > 0:
        add_button(
            "PREVIOUS ITEMS", (50, 485, 140, 32),
            "shop_prev_page", PANEL, small_font
        )

    if shop_page < total_pages - 1:
        add_button(
            "MORE ITEMS", (200, 485, 130, 32),
            "shop_next_page", PANEL, small_font
        )

    draw_panel((735, 225, 230, 310))
    draw_text("YOUR BUILD", 755, 245, BLUE_LIGHT, medium_font)

    y = 285

    if not selected:
        draw_text("No parts yet", 850, y, MUTED, font, True)
    else:
        for cat in categories:
            if cat in selected:
                name, price = selected[cat]
                draw_text(cat, 755, y, MUTED, small_font)
                draw_text(name[:19], 755, y + 17, WHITE, small_font)
                y += 45

                if y > 465:
                    draw_text("...", 755, y, MUTED, small_font)
                    break

    add_button("PREVIOUS", (30, 545, 130, 40), "previous", PANEL, font)
    add_button("NEXT", (175, 545, 130, 40), "next", PANEL, font)
    add_button(
        "BACK TO BUILD FLOOR", (325, 545, 250, 40),
        "floor", BLUE, font
    )
    add_button("MAIN MENU", (735, 545, 230, 40), "menu", PANEL, font)

    if message_timer > 0:
        draw_panel((610, 595, 355, 30), PANEL_HOVER)
        draw_text(message, 787, 610, WHITE, small_font, True)


# ==================================================
# BUILD SUMMARY
# ==================================================

def draw_finished():
    draw_background()

    draw_text("BUILD SUMMARY", 500, 65, BLUE_LIGHT, big_font, True)
    draw_text("Your current PC parts", 500, 112, MUTED, font, True)

    draw_panel((170, 155, 660, 350))
    y = 185

    for category in categories:
        if category in selected:
            name, price = selected[category]
        else:
            name, price = "Not purchased", 0

        draw_text(category, 205, y, BLUE_LIGHT, font)
        draw_text(name, 380, y, WHITE, small_font)
        draw_text(f"${price:,}" if price else "--", 745, y, GREEN, font)
        y += 39

    pygame.draw.line(screen, BORDER, (205, 435), (795, 435), 2)
    draw_text("TOTAL SPENT", 205, 455, MUTED, font)
    draw_text(f"${total_spent():,}", 745, 450, GREEN, medium_font)

    if is_complete():
        draw_text(
            f"Sale value: ${sale_value(selected):,}",
            500, 490, GREEN, small_font, True
        )
    else:
        draw_text(
            "Install all seven parts to sell or store this PC.",
            500, 490, MUTED, small_font, True
        )

    add_button(
        "BACK TO WORKSHOP", (170, 535, 190, 45),
        "floor", BLUE, font
    )
    add_button("SELL PC", (370, 535, 140, 45), "sell", (25, 105, 75), font)
    add_button("STORE PC", (520, 535, 140, 45), "store", PURPLE, font)
    add_button("MAIN MENU", (670, 535, 160, 45), "menu", PANEL, font)


# ==================================================
# INVENTORY
# ==================================================

def draw_inventory():
    draw_background()
    draw_header("PC INVENTORY", "Stored computers")

    income = sum(passive_income(pc) for pc in inventory)

    draw_text(
        f"Stored PCs: {len(inventory)}/{inventory_capacity}",
        35, 100, WHITE, medium_font
    )
    draw_text(f"Passive income: ${income} per second", 35, 135, GREEN, font)

    if not inventory:
        draw_panel((130, 220, 740, 150))
        draw_text(
            "Your inventory is empty.",
            500, 270, MUTED, medium_font, True
        )
        draw_text(
            "Complete a PC and select STORE PC to earn passive income.",
            500, 310, MUTED, small_font, True
        )

    for i in range(inventory_scroll, min(inventory_scroll + 6, len(inventory))):
        row = i - inventory_scroll
        y = 185 + row * 55
        pc = inventory[i]

        draw_panel((35, y, 930, 46))
        draw_text(f"PC {i + 1}", 50, y + 13, BLUE_LIGHT, font)
        draw_text(f"Cost: ${total_spent(pc):,}", 145, y + 13, WHITE, small_font)
        draw_text(f"Sale: ${sale_value(pc):,}", 320, y + 13, GREEN, small_font)
        draw_text(f"+${passive_income(pc)}/sec", 490, y + 13, PURPLE, small_font)

        add_button(
            "SELL PC", (790, y + 5, 150, 36),
            ("sell_inventory", i), BLUE, small_font
        )

    upgrade_cost = (
        2500 * (inventory_capacity - 2)
        if inventory_capacity < 15 else None
    )

    add_button("BACK", (35, 550, 150, 45), "floor", BLUE, font)
    add_button("UPGRADE", (205, 550, 230, 45), "upgrade", PURPLE, small_font)

    if inventory_scroll > 0:
        add_button("UP", (610, 550, 65, 45), "inventory_up", PANEL, font)

    if inventory_scroll + 6 < len(inventory):
        add_button("DOWN", (685, 550, 75, 45), "inventory_down", PANEL, font)

    add_button("MAIN MENU", (790, 550, 175, 45), "menu", PANEL, font)

    if upgrade_cost is not None:
        draw_text(
            f"Cost: ${upgrade_cost:,}",
            320, 605, MUTED, small_font, True
        )

    if message_timer > 0:
        draw_text(message, 500, 630, WHITE, small_font, True)


# ==================================================
# BUTTON ACTIONS
# ==================================================

def handle_action(action):
    global running, state, category_index, money
    global inventory_scroll, shop_page, music_muted
    global offline_popup_active

    if action == "close_offline_popup":
        offline_popup_active = False

    elif action == "quit":
        save_game()
        save_settings()
        running = False

    elif action == "start":
        state = "floor"

    elif action == "help":
        state = "help"

    elif action == "settings":
        state = "settings"

    elif action == "settings_back":
        save_settings()
        state = "menu"

    elif action == "toggle_mute":
        music_muted = not music_muted
        update_music_volume()
        save_settings()

    elif action == "back":
        state = "menu"

    elif action == "shop":
        state = "shop"

    elif action == "floor":
        state = "floor"

    elif action == "finish":
        state = "finished"

    elif action == "inventory":
        inventory_scroll = 0
        state = "inventory"

    elif action == "menu":
        save_game()
        state = "menu"

    elif action == "sell":
        sell_current_pc()

    elif action == "store":
        store_current_pc()

    elif action == "upgrade":
        upgrade_inventory()

    elif action == "inventory_up":
        inventory_scroll = max(0, inventory_scroll - 1)
        save_game()

    elif action == "inventory_down":
        if inventory_scroll + 6 < len(inventory):
            inventory_scroll += 1
            save_game()

    elif action == "shop_prev_page":
        shop_page = max(0, shop_page - 1)

    elif action == "shop_next_page":
        maximum = math.ceil(
            len(parts[categories[category_index]]) / SHOP_ITEMS_PER_PAGE
        ) - 1
        shop_page = min(maximum, shop_page + 1)

    elif isinstance(action, tuple) and action[0] == "sell_inventory":
        sell_inventory_pc(action[1])

    elif isinstance(action, tuple) and action[0] == "category":
        category_index = action[1]
        shop_page = 0
        save_game()

    elif action == "previous":
        category_index = (category_index - 1) % len(categories)
        shop_page = 0
        save_game()

    elif action == "next":
        category_index = (category_index + 1) % len(categories)
        shop_page = 0
        save_game()

    elif isinstance(action, tuple) and action[0] == "buy":
        _, category, item = action
        name, price = item

        old = selected.get(category)
        refund = old[1] if old else 0

        if old == item:
            notify("You already own this part!")

        elif money + refund < price:
            notify("Not enough money!")

        else:
            money = money + refund - price
            selected[category] = item

            save_game()
            notify(f"Purchased {name}!")


# ==================================================
# LOAD SAVED DATA
# ==================================================

load_game()
load_settings()
update_music_volume()


# ==================================================
# MAIN GAME LOOP
# ==================================================

while running:
    elapsed_ms = clock.tick(60)
    buttons = []

    if state in ("menu", "help", "settings"):
        play_music(MENU_MUSIC)
    else:
        play_music(BUILD_MUSIC)

    # Pay passive income while the game is running.
    income_timer += elapsed_ms

    if income_timer >= 1000:
        seconds = income_timer // 1000
        income_timer %= 1000

        earned_per_second = sum(
            passive_income(pc) for pc in inventory
        )

        earned = earned_per_second * seconds
        money += earned
        total_earned += earned

        if earned:
            save_game()

    # Draw current screen.
    if state == "menu":
        draw_menu()

        if offline_popup_active:
            draw_offline_popup()

    elif state == "help":
        draw_help()

    elif state == "settings":
        draw_settings()

    elif state == "floor":
        draw_floor()

    elif state == "shop":
        draw_shop()

    elif state == "finished":
        draw_finished()

    elif state == "inventory":
        draw_inventory()

    # Handle events.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            save_settings()
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if offline_popup_active and state == "menu":
                    offline_popup_active = False
                else:
                    save_game()

                    if state in ("help", "settings"):
                        state = "menu"
                    elif state == "shop":
                        state = "floor"
                    elif state in ("floor", "finished", "inventory"):
                        state = "menu"
                    else:
                        save_settings()
                        running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event_position(event.pos)
            slider_area = pygame.Rect(255, 255, 490, 45)

            # The popup blocks clicks on the menu behind it.
            if offline_popup_active and state == "menu":
                for rect, action in reversed(buttons):
                    if action == "close_offline_popup" and rect.collidepoint(pos):
                        handle_action(action)
                        break

            elif state == "settings" and slider_area.collidepoint(pos):
                dragging_volume = True
                music_volume = max(
                    0.0, min(1.0, (pos[0] - 270) / 460)
                )
                update_music_volume()
                save_settings()

            else:
                for rect, action in reversed(buttons):
                    if rect.collidepoint(pos):
                        handle_action(action)
                        break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging_volume = False

        elif event.type == pygame.MOUSEMOTION and dragging_volume:
            if state == "settings":
                pos_x = event_position(event.pos)[0]
                music_volume = max(
                    0.0, min(1.0, (pos_x - 270) / 460)
                )
                update_music_volume()
                save_settings()

        elif event.type == pygame.MOUSEWHEEL:
            if state == "inventory":
                if event.y > 0:
                    inventory_scroll = max(0, inventory_scroll - 1)
                    save_game()
                elif event.y < 0 and inventory_scroll + 6 < len(inventory):
                    inventory_scroll += 1
                    save_game()

            elif state == "shop":
                maximum = math.ceil(
                    len(parts[categories[category_index]]) / SHOP_ITEMS_PER_PAGE
                ) - 1

                if event.y > 0:
                    shop_page = max(0, shop_page - 1)
                elif event.y < 0:
                    shop_page = min(maximum, shop_page + 1)

    if message_timer > 0:
        message_timer -= 1

    display.blit(
        pygame.transform.smoothscale(screen, display.get_size()),
        (0, 0)
    )
    pygame.display.flip()


# ==================================================
# SAVE AND CLOSE
# ==================================================

save_game()
save_settings()

if MUSIC_ENABLED:
    pygame.mixer.music.stop()

pygame.quit()
sys.exit()