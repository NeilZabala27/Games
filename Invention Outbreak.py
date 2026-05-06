"""
=============================================================
  INVENTION OUTBREAK — Pygame Tower Defense / Shooter Game
=============================================================
  HOW THE GAME WORKS:
    - Enemies spawn from the top of the screen and march down.
    - You click to shoot them before they reach you.
    - Protect civilians (they heal you if they escape safely).
    - Every 3 waves a mini-boss appears, wave 5 is the final boss.
    - Survive all 5 waves to win!
=============================================================
"""

import pygame          # The main game library — handles graphics, input, sound
import os              # Used to work with file paths (not heavily used here but good practice)
import random          # Lets us pick random numbers and choices (spawn positions, monster types)
import math            # Gives us sqrt and sin for distance calculations and animations

# ── Boot pygame up ──────────────────────────────────────────
pygame.init()          # Start ALL pygame systems (graphics, input, etc.) — always call this first
pygame.mixer.init()    # Start the audio system separately — needed before playing any sound

# ── Window Setup ────────────────────────────────────────────
WINDOW_WIDTH  = 1280   # How wide the game window is, in pixels
WINDOW_HEIGHT = 700    # How tall the game window is, in pixels

# Create the actual window — this is what the player sees
window_screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

pygame.display.set_caption("Invention Outbreak")   # The title that appears in the window title bar
clock = pygame.time.Clock()                         # Controls how fast the game loop runs (FPS limiter)

pygame.mouse.set_visible(False)   # Hide the default OS cursor — we'll draw our own crosshair aim

# ── Background Images ────────────────────────────────────────
# Load the in-game background image from the image folder
BG = pygame.image.load('image/easy-medium.jpg')
# Resize it to exactly fill the window (1280x700)
scaled_image = pygame.transform.scale(BG, (1280, 700))

# Load the main menu background (different art from the in-game BG)
Main_BG = pygame.image.load('image/Main menu BG.jpg')
scaled_mainBG = pygame.transform.scale(Main_BG, (1280, 700))   # Resize it to fill the window too

# ── Fonts ────────────────────────────────────────────────────
# Load our custom pixel font at different sizes for different uses
pixel_font = pygame.font.Font('Game Shark.otf', 28)   # Medium — used for HUD text like score/HP
big_font   = pygame.font.Font('Game Shark.otf', 70)   # Large — used for titles and wave banners
small_font = pygame.font.Font('Game Shark.otf', 20)   # Small — used for descriptions and sub-labels

# ── Background Music ─────────────────────────────────────────
pygame.mixer.music.load('Sound/bg_music.mp3')   # Load the music file into the mixer
pygame.mixer.music.set_volume(0.3)              # 30% volume — loud enough to hear, quiet enough to not annoy
pygame.mixer.music.play(-1)                     # -1 means loop forever until we stop it

# ── Sound Effects ────────────────────────────────────────────
gun_shot_sound  = pygame.mixer.Sound('Sound/gun_shot.wav')
reload_sound    = pygame.mixer.Sound('Sound/reload_sound.mp3')
gun_shot_sound.set_volume(0.6)    # Adjust volume 0.0 to 1.0
reload_sound.set_volume(0.5)


# =============================================================
#  SPRITE SHEET LOADING — SLIME
# =============================================================
# A "sprite sheet" is one big image that contains multiple animation frames side by side.
# We slice it up manually to get each frame.

slime_img = pygame.image.load('image/slime(1).png').convert_alpha()
# .convert_alpha() converts the image to a format pygame can draw faster, keeping transparency

# Figure out the width of one frame (the sheet has 6 frames in a row)
frame_width  = slime_img.get_width() // 6    # Integer divide total width by 6 frames
frame_height = slime_img.get_height()        # Height is the full height (only 1 row of frames)

# Loop through all 6 frames and cut each one out
frames = []
for i in range(6):
    # pygame.Rect(x, y, width, height) — defines a rectangle to cut from the sheet
    frame = slime_img.subsurface(
        pygame.Rect(i * frame_width, 0, frame_width, frame_height)
    )
    frame = pygame.transform.scale(frame, (200, 200))   # Resize each frame to 200x200 pixels
    frames.append(frame)                                 # Add the frame to our list


# =============================================================
#  SPRITE SHEET LOADING — GOBLIN
# =============================================================
goblin_img = pygame.image.load('image/Goblin(1).png').convert_alpha()

sheet_cols = 5   # The goblin sheet has 5 columns (frames per row)
sheet_rows = 5   # And 5 rows (one per animation state)

frame_width  = goblin_img.get_width()  // sheet_cols   # Width of one goblin frame
frame_height = goblin_img.get_height() // sheet_rows   # Height of one goblin frame

def get_rows(sheet, row, cols, fw, fh, selected_cols):
    """
    Helper function that cuts specific frames from a specific row of a sprite sheet.
    
    sheet         — the full sprite sheet image (not used directly, but passed for clarity)
    row           — which row of the sheet to read from (0 = top row)
    cols          — total number of columns in the sheet (used for reference)
    fw, fh        — width and height of a single frame
    selected_cols — a list of column indices we want (e.g. [0, 1, 2] for first 3 frames)
    """
    frames = []
    for col in selected_cols:
        frame = goblin_img.subsurface(
            pygame.Rect(
                col * fw,    # X position: move right by frame-width for each column
                row * fh,    # Y position: move down by frame-height for each row
                fw,
                fh
            )
        )
        frames.append(frame)
    return frames

# Cut out the specific animation frames for each goblin state
goblin_idle_frames   = get_rows(goblin_img, 0, sheet_cols, frame_width, frame_height, selected_cols=[0])          # Row 0, just 1 frame
goblin_walk_frames   = get_rows(goblin_img, 1, sheet_cols, frame_width, frame_height, selected_cols=[0, 1, 2, 3, 4])  # Row 1, all 5 frames
goblin_attack_frames = get_rows(goblin_img, 2, sheet_cols, frame_width, frame_height, selected_cols=[0, 1, 2, 4])  # Row 2, skip frame 3


# =============================================================
#  SPRITE SHEET LOADING — SKELETON
# =============================================================
skeleton_img = pygame.image.load('image/Skeleton(1).png').convert_alpha()

skeleton_sheet_cols = 7   # 7 frames per row
skeleton_sheet_rows = 4   # 4 animation rows

skeleton_frame_width  = skeleton_img.get_width()  // skeleton_sheet_cols
skeleton_frame_height = skeleton_img.get_height() // skeleton_sheet_rows

def skeleton_get_rows(row, selected_cols):
    """Same idea as get_rows() above, but hardcoded to use skeleton_img."""
    frames = []
    for col in selected_cols:
        frame = skeleton_img.subsurface(
            pygame.Rect(
                col * skeleton_frame_width,
                row * skeleton_frame_height,
                skeleton_frame_width,
                skeleton_frame_height
            )
        )
        frames.append(frame)
    return frames

# Slice out skeleton animations from the sheet
skeleton_idle_frames    = skeleton_get_rows(0, range(3))       # Row 0, first 3 frames = idle
skeleton_attack_frames1 = skeleton_get_rows(0, [4, 5, 6])     # Row 0, last 3 frames = start of attack
skeleton_attack_frames2 = skeleton_get_rows(1, range(5))      # Row 1, all 5 frames = rest of attack
skeleton_death_frames   = skeleton_get_rows(3, range(7))      # Row 3, all 7 frames = death

# Combine the two attack frame lists into one continuous attack animation
skeleton_attack = skeleton_attack_frames1 + skeleton_attack_frames2


# =============================================================
#  SPRITE SHEET LOADING — MINOTAUR (Mini-boss, Easy mode)
# =============================================================
minotaur_img = pygame.image.load('image/Minotaur(1).png').convert_alpha()

sheet_cols = 6   # Reusing the same variable name — 6 columns for minotaur
sheet_rows = 6   # 6 rows

frame_width  = minotaur_img.get_width()  // sheet_cols
frame_height = minotaur_img.get_height() // sheet_rows

def get_miniboss_rows(sheet, row, cols, fw, fh, selected_cols):
    """Same as get_rows but reads from minotaur_img."""
    frames = []
    for col in selected_cols:
        frame = minotaur_img.subsurface(
            pygame.Rect(col * fw, row * fh, fw, fh)
        )
        frames.append(frame)
    return frames

minotaur_walk           = get_miniboss_rows(minotaur_img, 0, sheet_cols, frame_width, frame_height, range(6))        # Row 0: walk cycle
minotaur_attack_frames1 = get_miniboss_rows(minotaur_img, 1, sheet_cols, frame_width, frame_height, range(6))        # Row 1 all: first half of attack
minotaur_attack_frames2 = get_miniboss_rows(minotaur_img, 1, sheet_cols, frame_width, frame_height, selected_cols=[0, 1])  # Loop back to beginning of row 1
minotaur_death_frame    = get_miniboss_rows(minotaur_img, 5, sheet_cols, frame_width, frame_height, [1, 2, 3, 4, 5]) # Row 5: death

minotaur_attack = minotaur_attack_frames1 + minotaur_attack_frames2   # Combined attack animation


# =============================================================
#  SPRITE SHEET LOADING — DRAGON (Mini-boss, Medium mode)
# =============================================================
dragon_img = pygame.image.load('image/Dragon.png').convert_alpha()

dragon_sheet_cols = 7
dragon_sheet_rows = 7

dragon_frame_width  = dragon_img.get_width()  // dragon_sheet_cols
dragon_frame_height = dragon_img.get_height() // dragon_sheet_rows

def dragon_get_rows(row, selected_cols):
    """Reads frames from dragon_img at the given row and column indices."""
    frames = []
    for col in selected_cols:
        frame = dragon_img.subsurface(
            pygame.Rect(
                col * dragon_frame_width,
                row * dragon_frame_height,
                dragon_frame_width,
                dragon_frame_height
            )
        )
        frames.append(frame)
    return frames

# Slice out dragon animations
dragon_walking_frames       = dragon_get_rows(0, range(7))         # Row 0: walk
dragon_first_attack_frames  = dragon_get_rows(1, [1, 2, 3, 4])    # Row 1, frames 1-4: first attack
dragon_second_attack_frames1= dragon_get_rows(2, [3, 4, 5, 6])    # Row 2 partial: second attack start
dragon_second_attack_frames2= dragon_get_rows(3, range(6))        # Row 3: second attack continuation
dragon_third_attack_frames  = dragon_get_rows(5, range(7))        # Row 5: third attack
dragon_death_frames         = dragon_get_rows(6, [1, 2, 3, 4, 5, 6])  # Row 6: death

# Combine parts of the second attack into one smooth animation
dragon_second_attack = dragon_second_attack_frames1 + dragon_second_attack_frames2


# =============================================================
#  SPRITE SHEET LOADING — SCIENTIST (Mini-boss, Hard mode)
# =============================================================
scientist_img = pygame.image.load('image/Scientist.png').convert_alpha()

scientist_sheet_cols = 8
scientist_sheet_rows = 7

scientist_frame_width  = scientist_img.get_width()  // scientist_sheet_cols
scientist_frame_height = scientist_img.get_height() // scientist_sheet_rows

def scientist_get_rows(row, selected_cols):
    """Reads frames from scientist_img."""
    frames = []
    for col in selected_cols:
        frame = scientist_img.subsurface(
            pygame.Rect(
                col * scientist_frame_width,
                row * scientist_frame_height,
                scientist_frame_width,
                scientist_frame_height
            )
        )
        frames.append(frame)
    return frames

# Each attack is split across two rows of the sheet, so we combine them
scientist_first_attack_frames1  = scientist_get_rows(2, [1, 2, 3, 4, 5, 6, 7])
scientist_first_attack_frames2  = scientist_get_rows(3, range(2))
scientist_second_attack_frames1 = scientist_get_rows(3, [2, 3, 4, 5, 6, 7])
scientist_second_attack_frames2 = scientist_get_rows(4, range(4))
scientist_third_attack_frames1  = scientist_get_rows(4, [4, 5, 6, 7])
scientist_third_attack_frames2  = scientist_get_rows(5, range(4))
scientist_death_frames          = scientist_get_rows(6, range(6))

# Glue the two halves of each attack together
scientist_first_attack  = scientist_first_attack_frames1  + scientist_first_attack_frames2
scientist_second_attack = scientist_second_attack_frames1 + scientist_second_attack_frames2
scientist_third_attack  = scientist_third_attack_frames1  + scientist_third_attack_frames2


# =============================================================
#  SPRITE SHEET LOADING — DEMON LORD (Final Boss, all modes)
# =============================================================
demon_lord_img = pygame.image.load('image/Demon Lord(1).png').convert_alpha()

dl_sheet_cols = 9
dl_sheet_rows = 8

dl_fw = demon_lord_img.get_width()  // dl_sheet_cols   # Width of one Demon Lord frame
dl_fh = demon_lord_img.get_height() // dl_sheet_rows   # Height of one Demon Lord frame

def get_finalboss_rows(row, selected_cols):
    """Reads frames from demon_lord_img."""
    frames = []
    for col in selected_cols:
        frame = demon_lord_img.subsurface(
            pygame.Rect(col * dl_fw, row * dl_fh, dl_fw, dl_fh)
        )
        frames.append(frame)
    return frames

# Slice out all Demon Lord animations — he has many phases!
dl_idle_frames             = get_finalboss_rows(1, [4, 5, 6])
dl_walking_frames1         = get_finalboss_rows(0, range(9))       # Walk part 1 (full row 0)
dl_walking_frames2         = get_finalboss_rows(1, range(4))       # Walk part 2 (first 4 of row 1)
dl_first_attack_frames1    = get_finalboss_rows(1, [7, 8])
dl_first_attack_frames2    = get_finalboss_rows(2, range(9))
dl_first_attack_frames3    = get_finalboss_rows(3, range(3))
dl_transformation_frames1  = get_finalboss_rows(3, [4, 5, 6, 7, 8])  # Transformation begins here
dl_transformation_frames2  = get_finalboss_rows(4, range(1))
dl_second_attack_frames    = get_finalboss_rows(4, range(9))       # Post-transform attack 1
dl_third_attack_frames     = get_finalboss_rows(5, range(9))       # Post-transform attack 2
dl_fourth_attack_frames    = get_finalboss_rows(6, range(9))       # Post-transform attack 3
dl_death_frames            = get_finalboss_rows(7, range(9))       # Death sequence

# Combine multi-part animations
dl_walking      = dl_walking_frames1 + dl_walking_frames2
dl_first_attack = dl_first_attack_frames1 + dl_first_attack_frames2 + dl_first_attack_frames3
dl_transformation = dl_transformation_frames1 + dl_transformation_frames2


# =============================================================
#  SPRITE SHEET LOADING — CIVILIANS (Male & Female)
# =============================================================
# Male civilian
male_civilian = pygame.image.load('image/male civilian(1).png').convert_alpha()

sheet_cols = 6   # 6 columns in the civilian sheet
sheet_rows = 4   # 4 rows

male_frame_width  = male_civilian.get_width()  // sheet_cols
male_frame_height = male_civilian.get_height() // sheet_rows

male_run_frames  = []   # Will hold the run animation frames
male_dead_frames = []   # Will hold the death animation frames

# Row 1 = run animation (6 frames across)
for col in range(6):
    frame = male_civilian.subsurface(pygame.Rect(col * male_frame_width, 1 * male_frame_height, male_frame_width, male_frame_height))
    male_run_frames.append(frame)

# Row 3 = death animation (5 frames)
for col in range(5):
    frame = male_civilian.subsurface(pygame.Rect(col * male_frame_width, 3 * male_frame_height, male_frame_width, male_frame_height))
    male_dead_frames.append(frame)

# Female civilian — same process, different sheet
female_civilian = pygame.image.load('image/female civilian(1).png').convert_alpha()

sheet_cols = 7   # Female sheet has 7 columns
sheet_rows = 4

female_frame_width  = female_civilian.get_width()  // sheet_cols
female_frame_height = female_civilian.get_height() // sheet_rows

female_run_frames  = []
female_dead_frames = []

# Row 0 = run animation for female (6 frames)
for col in range(6):
    frame = female_civilian.subsurface(pygame.Rect(col * female_frame_width, 0 * female_frame_height, female_frame_width, female_frame_height))
    female_run_frames.append(frame)

# Row 3 = death animation for female (5 frames)
for col in range(5):
    frame = female_civilian.subsurface(pygame.Rect(col * female_frame_width, 3 * female_frame_height, female_frame_width, female_frame_height))
    female_dead_frames.append(frame)

# Store both civilian types in a dictionary so we can look them up by name
CIVILIAN_TYPE = {
    'male':   {'run': male_run_frames,   'dead': male_dead_frames},
    'female': {'run': female_run_frames, 'dead': female_dead_frames},
}

# ── Bullet Image ─────────────────────────────────────────────
bullet_image = pygame.image.load('image/pixel bullets.png').convert_alpha()
bullet_image = pygame.transform.scale(bullet_image, (100, 100))   # Scale to 100x100 (we'll shrink it again when drawing)


# =============================================================
#  DIFFICULTY SETTINGS
# =============================================================
# Each difficulty key maps to a dictionary of settings.
# The game reads from this when spawning enemies, setting HP, ammo, etc.

LEVELS = {
    'Easy': {
        'spawn_interval':    300,   # Ticks between spawns — higher = slower spawns
        'slime_speed':       1,     # How fast slimes move toward you
        'slime_hp':          1,     # How many hits slimes can take
        'goblin_speed':      1,
        'goblin_hp':         2,
        'skeleton_speed':    1,
        'skeleton_hp':       4,
        'minotaur_hp':       20,    # Easy mini-boss is the Minotaur
        'minotaur_speed':    1,
        'demon_lord_hp':     30,    # Final boss HP on Easy
        'demon_lord_speed':  1,
        'shoot_delay':       10,    # Frames between each shot (lower = faster fire rate)
        'reload_time':       60,    # Frames to reload (60 frames = 1 second at 60fps)
        'max_ammo':          6,     # How many bullets before you must reload
        'color':             (80, 200, 80),     # Green color used in UI for Easy
        'max_enemies':       15,    # Total enemies that will ever spawn this run
        'max_civilians':     5,     # Maximum civilians that will appear
        'enemies_per_wave':  3,     # How many enemies spawn per wave
        'description':       'Slow spawn | 6 ammo | Fast reload',
    },
    'Medium': {
        'spawn_interval':    180,
        'slime_speed':       1,
        'slime_hp':          2,
        'goblin_speed':      1,
        'goblin_hp':         3,
        'skeleton_speed':    1,
        'skeleton_hp':       6,
        'dragon_hp':         40,    # Medium mini-boss is the Dragon
        'dragon_speed':      1,
        'demon_lord_hp':     80,    # Final boss is tougher on Medium
        'demon_lord_speed':  1,
        'shoot_delay':       10,
        'reload_time':       60,
        'max_ammo':          6,
        'color':             (220, 180, 0),     # Yellow for Medium
        'max_enemies':       20,
        'max_civilians':     5,
        'enemies_per_wave':  3,
        'description':       'Normal spawn | 6 ammo | Normal reload',
    },
    'Hard': {
        'spawn_interval':    180,
        'slime_speed':       1,
        'slime_hp':          4,     # Slimes are tankier on Hard
        'goblin_speed':      1,
        'goblin_hp':         6,
        'skeleton_speed':    1,
        'skeleton_hp':       8,
        'scientist_hp':      20,    # Hard mini-boss is the Scientist
        'scientist_speed':   1,
        'demon_lord_hp':     50,
        'demon_lord_speed':  2,     # Final boss moves faster on Hard
        'shoot_delay':       10,
        'reload_time':       60,
        'max_ammo':          6,
        'color':             (220, 60, 60),     # Red for Hard
        'max_enemies':       35,
        'max_civilians':     5,
        'enemies_per_wave':  3,
        'description':       'Normal spawn | 6 ammo | Slow reload',
    },
}


# =============================================================
#  SPAWN ZONES
# =============================================================
# We split the screen horizontally into 6 zones.
# Each zone is a (min_x, max_x) range.
# When spawning an enemy, we pick a zone that isn't already occupied.

SPAWN_ZONES = [
    (50,   250),    # Left zone
    (250,  450),    # Center-left zone
    (450,  650),    # Center zone
    (650,  850),    # Center-right zone
    (850,  1100),   # Right zone
    (1100, 1230),   # Far-right zone
]

used_zones = []   # Tracks which zones are currently occupied (not heavily used here, zones picked per-spawn)

def get_spawn_x(sprite_group_list):
    """
    Finds an X position to spawn a new enemy that isn't too close to existing ones.
    
    sprite_group_list — a list of pygame sprite groups (e.g. slimes, goblins)
                        We check all of them for collisions.
    Returns an X coordinate that falls inside a free zone.
    """
    # Collect the center X of every existing enemy on screen
    all_occupied = []
    for group in sprite_group_list:
        for sprite in group:
            all_occupied.append(sprite.rect.centerx)

    # Shuffle zones so we don't always check left-to-right
    random.shuffle(SPAWN_ZONES)

    for zone_min, zone_max in SPAWN_ZONES:
        # Check whether any existing enemy is already in this zone
        occupied = False
        for x in all_occupied:
            if zone_min < x < zone_max:
                occupied = True
                break
        if not occupied:
            return random.randint(zone_min, zone_max)   # Pick a random X inside the free zone

    # All zones occupied — just pick a completely random X as a fallback
    return random.randint(50, WINDOW_WIDTH - 50)


# =============================================================
#  SLIME CLASS
# =============================================================
class Slime(pygame.sprite.Sprite):
    """
    The weakest enemy. Slides straight down toward the center-bottom.
    Grows bigger as it approaches the player (perspective trick).
    No attack — just reaching the bottom counts as damage.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()   # ALWAYS call super().__init__() first in a pygame Sprite subclass

        self.frames = frames         # The 6 slime animation frames we loaded earlier
        self.index  = 0              # Which frame we're currently showing (floats for smooth animation)
        self.image  = self.frames[self.index]   # pygame needs self.image to know what to draw
        self.rect   = self.image.get_rect()     # pygame needs self.rect to know where to draw it

        self.rect.centerx = spawn_x   # Start at the given X position
        self.rect.y       = -120      # Start above the screen (so it "slides in" from the top)

        self.speed   = speed   # Pixels per frame the slime moves
        self.hp      = hp      # How many hits it can take before dying
        self.spawning = True   # Flag for "still entering the screen" (not used much here but useful to track)
        self.reach_bottom = False   # True once the slime passes the bottom edge
        self.escaped      = False   # True once it has fully left the screen (triggers player damage)

        # Hit stun — when shot, the slime freezes briefly
        self.hit_stun      = 0    # Countdown timer (frames). When > 0, the slime can't move
        self.HIT_STUN_TIME = 15   # How many frames of stun each hit gives (15 frames ≈ 0.25 sec)

        # Target: the slime always moves toward the center-bottom of the screen
        self.target_x = WINDOW_WIDTH  // 2   # Horizontal center
        self.target_y = WINDOW_HEIGHT + 100  # A bit below the bottom edge

        # Size scaling — slimes appear small at the top and grow as they descend
        self.base_size    = 120   # Starting size in pixels (small, far away)
        self.max_size     = 300   # Maximum size in pixels (large, close up)
        self.current_size = self.base_size

        # Pre-calculate the velocity vector toward the target
        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        """
        Calculates the X and Y velocity to move toward the target at the given speed.
        
        We use vector math:
          1. Find the direction vector (dx, dy) from current position to target.
          2. Find its length (distance).
          3. Normalize it (divide by distance) to get a unit vector of length 1.
          4. Multiply by speed to get the actual velocity.
        """
        dx = self.target_x - self.rect.centerx    # How far we need to go horizontally
        dy = self.target_y - self.rect.centery    # How far we need to go vertically
        distance = math.sqrt(dx**2 + dy**2)       # Pythagorean theorem: total distance

        if distance != 0:
            vel_x = (dx / distance) * self.speed   # Normalized X component × speed
            vel_y = (dy / distance) * self.speed   # Normalized Y component × speed
        else:
            vel_x = 0   # Already at the target — don't move
            vel_y = 0
        return vel_x, vel_y

    def animation_state(self):
        """Advances the animation by a small increment each frame."""
        self.index += 0.1             # Add 0.1 each frame — cycles through 6 frames smoothly
        if self.index >= len(self.frames):
            self.index = 0            # Wrap back to frame 0 when we reach the end
        self.image = self.frames[int(self.index)]   # int() converts the float index to a whole number

    def take_hit(self, damage=1):
        """Called when a bullet hits this slime."""
        self.hp       -= damage          # Reduce HP by the damage amount
        self.hit_stun  = self.HIT_STUN_TIME   # Start the stun timer

    def separate(self, all_sprites):
        """
        Pushes this slime away from other sprites if they overlap.
        This prevents enemies from stacking on top of each other.
        """
        for other in all_sprites:
            if other is self:
                continue   # Skip ourselves — we don't need to push away from ourselves

            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            distance = math.sqrt(dx**2 + dy**2)

            # min_dist is how close two sprites can get before we push them apart
            min_dist = (self.current_size + other.current_size) // 2

            if 0 < distance < min_dist:   # They're overlapping
                overlap = min_dist - distance   # How much they're overlapping
                # Push this slime away from the other, proportional to the overlap
                self.rect.x += int((dx / distance) * overlap * 0.5)
                self.rect.y += int((dy / distance) * overlap * 0.5)

    def update(self, all_sprites):
        """
        Called every frame by the game loop.
        Updates position, animation, and size.
        """
        # ── If stunned, freeze movement but still animate ──
        if self.hit_stun > 0:
            self.hit_stun -= 1   # Count down the stun timer

            self.animation_state()
            # Still update the size scaling during stun (so it doesn't snap when stun ends)
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))   # 0.0 at top, 1.0 at bottom
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center   # Save center before we resize the rect
            frame  = self.frames[int(self.index)]
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)   # Re-center the rect after resize
            return   # Skip the rest of update while stunned

        # ── Move toward the target ──
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Scale size based on vertical position ──
        # progress: 0.0 = top of screen, 1.0 = bottom of screen
        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        # Resize the image to the new size, keeping the sprite centered
        center     = self.rect.center
        self.image = pygame.transform.scale(
            self.frames[int(self.index)],
            (self.current_size, self.current_size)
        )
        self.rect  = self.image.get_rect(center=center)

        self.separate(all_sprites)   # Push away from overlapping sprites

        # ── Keep the slime inside the screen horizontally ──
        if self.rect.left  < 0:            self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH

        # ── If slime passes the bottom, mark it as escaped ──
        if self.rect.top > WINDOW_HEIGHT:
            self.escaped      = True
            self.reach_bottom = True

        self.animation_state()

    def draw(self, screen):
        """Draws the slime at its current size and position."""
        frame  = self.frames[int(self.index)]
        scaled = pygame.transform.scale(frame, (self.current_size, self.current_size))

        draw_rect = scaled.get_rect(center=self.rect.center)
        screen.blit(scaled, draw_rect)   # blit = "copy image onto surface at position"

    def is_at_center(self):
        """Returns True if the slime has reached the center-bottom target point."""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        return distance < 20   # "Close enough" threshold of 20 pixels


# =============================================================
#  GOBLIN CLASS
# =============================================================
class Goblin(pygame.sprite.Sprite):
    """
    Medium-strength enemy. Walks down the screen, then stops partway
    and enters an attack animation. Does periodic damage while attacking.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        # Store all animation frame lists in a dictionary, keyed by state name
        self.animation = {
            "idle":   goblin_idle_frames,
            "walk":   goblin_walk_frames,
            "attack": goblin_attack_frames
        }
        self.state = 'walk'             # Start in walking state
        self.index = 0.0               # Current animation frame (float for smooth stepping)
        self.image = self.animation['walk'][0]   # Initial image = first walk frame
        self.rect  = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -120    # Spawn above the screen

        self.speed = speed
        self.hp    = hp
        self.spawning = True

        self.base_size    = 200
        self.max_size     = 500
        self.current_size = self.base_size

        # The Y position where the goblin stops walking and starts attacking
        self.attack_range = WINDOW_HEIGHT * 0.50   # 50% down the screen

        # Attack timing
        self.attack_timer  = 0     # Counts up each frame while attacking
        self.delay_attack  = 120   # After this many frames in attack state, deal damage
        self.damage_dealt  = False

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        self.target_x = WINDOW_WIDTH  // 2
        self.target_y = WINDOW_HEIGHT + 100

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        """Same vector-math velocity calculation as Slime."""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        """
        Switches the goblin's animation state safely.
        Resets the frame index so the new animation starts from the beginning.
        """
        if self.state != new_state:   # Only switch if the state is actually changing
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        """Advances animation at different speeds depending on the current state."""
        if self.state == 'attack':
            speed = 0.035   # Slower attack animation (more dramatic)
        else:
            speed = 0.1     # Faster walk animation

        frames = self.animation[self.state]
        self.index += speed

        if self.index >= len(frames):
            self.index = 0.0   # Loop the animation

    def get_current_frame(self):
        """Returns the current frame safely (prevents out-of-bounds errors)."""
        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)   # Never go past the last frame
        return frames[safe_index]

    def take_hit(self, damage=1):
        """Reduces HP and applies hit stun."""
        self.hp       -= damage
        self.hit_stun  = self.HIT_STUN_TIME

    def separate(self, all_sprites):
        """Pushes the goblin away from overlapping sprites (same logic as Slime)."""
        for other in all_sprites:
            if other is self:
                continue
            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            min_dist = (self.current_size + other.current_size) // 2
            if 0 < distance < min_dist:
                overlap = min_dist - distance
                self.rect.x += int((dx / distance) * overlap * 0.5)
                self.rect.y += int((dy / distance) * overlap * 0.5)

    def update(self, all_sprites):
        """Main update — runs every frame."""
        # ── Freeze during hit stun ──
        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        # ── Move toward target ──
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Switch to attack when goblin has walked far enough down ──
        if self.rect.y >= self.attack_range + 10:
            self.set_state('attack')
            self.vel_x = 0    # Stop moving when attacking
            self.vel_y = 0
        elif self.rect.y < self.attack_range - 20:
            self.set_state('walk')

        self.animation_state()

        # ── Size scaling (same as Slime — bigger near the bottom) ──
        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)

        center     = self.rect.center
        self.image = pygame.transform.scale(frames[safe_index], (self.current_size, self.current_size))
        self.rect  = self.image.get_rect(center=center)

        self.separate(all_sprites)

        # ── Clamp horizontal position inside screen ──
        if self.rect.left  < 0:            self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH
        if self.rect.top   > WINDOW_HEIGHT: self.kill()   # Remove if it sneaks past the bottom

        if self.is_at_center():
            self.kill()   # Remove if it reaches the exact center target

    def dealt_damage(self):
        """
        Returns True once per attack cycle when it's time to deal damage.
        The game loop calls this every frame and deducts HP when it returns True.
        """
        if self.state == 'attack':
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:   # Enough frames have passed
                self.attack_timer = 0                    # Reset timer for next attack cycle
                return True
        else:
            self.attack_timer = 0   # Not attacking — reset timer
        return False

    def draw(self, window_screen):
        """Draws the goblin to the screen."""
        window_screen.blit(self.image, self.rect)

    def is_at_center(self):
        """Returns True if the goblin reached the center-bottom target."""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        return distance < 20


# =============================================================
#  SKELETON CLASS
# =============================================================
class Skeleton(pygame.sprite.Sprite):
    """
    Tougher enemy with a death animation. It walks to the upper third of
    the screen, locks into position, and then shoots/attacks from there.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        self.animation = {
            "idle":   skeleton_idle_frames,
            "attack": skeleton_attack,        # Combined attack animation
            "death":  skeleton_death_frames
        }
        self.state = 'idle'
        self.index = 0.0
        self.image = self.animation['idle'][0]
        self.rect  = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -120

        self.speed = speed
        self.hp    = hp

        self.base_size    = 200
        self.max_size     = 500
        self.current_size = self.base_size

        # The skeleton stops at 35% down the screen (higher up than goblins)
        self.stop_y     = WINDOW_HEIGHT * 0.35
        self.positioned = False   # Becomes True once the skeleton reaches its stop point
        self.dying      = False   # Becomes True when HP reaches 0

        self.attack_timer = 0
        self.delay_attack = 90    # Attacks faster than goblins

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        # Target is the stop_y position (not the very bottom like slimes)
        self.target_x = WINDOW_WIDTH // 2
        self.target_y = int(self.stop_y)

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        """Calculates velocity toward the stop target."""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        """Switches animation state, resetting the frame counter."""
        if self.state != new_state:
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        """Advances animation. Death animation plays once and then kills the sprite."""
        if self.state == 'attack':
            speed = 0.1
        else:
            speed = 0.08   # Idle and death are slightly slower

        frames = self.animation[self.state]
        self.index += speed

        if self.index >= len(frames):
            if self.state == 'death':
                self.kill()   # Remove from all groups once death animation finishes
                return
            self.index = 0.0   # Loop other animations

    def get_current_frame(self):
        """Returns the current frame safely."""
        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)
        return frames[safe_index]

    def separate(self, all_sprites):
        """Push away from other sprites to avoid stacking."""
        for other in all_sprites:
            if other is self:
                continue
            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            min_dist = (self.current_size + other.current_size) // 2
            if 0 < distance < min_dist:
                overlap = min_dist - distance
                self.rect.x += int((dx / distance) * overlap * 0.3)
                self.rect.y += int((dy / distance) * overlap * 0.3)

    def take_hit(self):
        """Reduces HP by 1. Triggers death animation at 0 HP."""
        self.hp -= 1
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.set_state('death')   # Switch to death animation
            self.vel_x = 0
            self.vel_y = 0

    def dealt_damage(self):
        """Returns True once per attack cycle while the skeleton is in position and alive."""
        if self.state == 'attack' and self.positioned and not self.dying:
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:
                self.attack_timer = 0
                return True
        else:
            if not self.positioned:
                self.attack_timer = 0   # Don't count while still walking
        return False

    def update(self, all_sprites):
        """Main update — runs every frame."""
        # ── Stun freeze ──
        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        self.animation_state()

        # ── If dying, just play death anim and return ──
        if self.dying:
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center     = self.rect.center
            frame      = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        # ── Walk to position, then lock in place ──
        if not self.positioned:
            self.vel_x, self.vel_y = self.get_velocity()

            self.rect.x += self.vel_x
            self.rect.y += self.vel_y
            self.set_state('idle')

            # Check if close enough to the stop point
            if abs(self.rect.centery - self.stop_y) < 5:
                self.rect.centery = int(self.stop_y)   # Snap exactly into position
                self.vel_x        = 0
                self.vel_y        = 0
                self.positioned   = True
                self.set_state('attack')   # Start attacking now
        else:
            self.set_state('attack')   # Already positioned — keep attacking

        # ── Grow bigger as it descends ──
        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        center     = self.rect.center
        frame      = self.get_current_frame()
        self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
        self.rect  = self.image.get_rect(center=center)

        self.separate(all_sprites)

        if self.rect.left  < 0:            self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH

    def draw(self, surface):
        """Draw the skeleton to the surface."""
        surface.blit(self.image, self.rect)


# =============================================================
#  MINOTAUR CLASS  (Mini-boss — Easy mode)
# =============================================================
class Minotaur(pygame.sprite.Sprite):
    """
    The Easy difficulty mini-boss. Much tankier than regular enemies.
    Has a health bar displayed at the top of the screen.
    Walks down, then enters an attack loop.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        self.animation = {
            'walk':   minotaur_walk,
            'attack': minotaur_attack,
            'death':  minotaur_death_frame
        }
        self.state = 'walk'
        self.index = 0.0
        self.image = self.animation['walk'][0]
        self.rect  = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -50

        self.speed    = speed
        self.hp       = hp
        self.max_hp   = hp         # Save the starting HP so we can draw the health bar ratio
        self.display_hp = hp       # Smooth display HP (could be animated)
        self.dying    = False
        self.spawning = True

        self.base_size    = 200
        self.max_size     = 1000   # Bosses get MUCH larger than regular enemies
        self.current_size = self.base_size

        self.attack_range = WINDOW_HEIGHT * 0.36

        self.attack_timer  = 0
        self.delay_attack  = 180   # Bosses attack slower but hit harder
        self.damage_dealt  = False

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        self.target_x = WINDOW_WIDTH  // 2
        self.target_y = WINDOW_HEIGHT + 100

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        """Attack is slower, death is very fast for dramatic effect."""
        if self.state == 'attack':
            speed = 0.035
        elif self.state == 'death':
            speed = 0.04     # Death animation plays very quickly
        else:
            speed = 0.1

        frames = self.animation[self.state]
        self.index += speed

        if self.index >= len(frames):
            if self.state == 'death':
                self.kill()   # Remove the Minotaur once death finishes
                return
            self.index = 0.0

    def get_current_frame(self):
        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)
        return frames[safe_index]

    def take_hit(self):
        """Reduces HP. At 0 HP, switches to death state."""
        self.hp -= 1
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.set_state('death')
            self.vel_x = 0
            self.vel_y = 0

    def separate(self, all_sprites):
        for other in all_sprites:
            if other is self:
                continue
            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            min_dist = (self.current_size + other.current_size) // 2
            if 0 < distance < min_dist:
                overlap = min_dist - distance
                self.rect.x += int((dx / distance) * overlap * 0.5)
                self.rect.y += int((dy / distance) * overlap * 0.5)

    def dealt_damage(self):
        """Returns True once per attack cycle while not dying."""
        if self.state == 'attack' and not self.dying:
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:
                self.attack_timer = 0
                return True
        else:
            self.attack_timer = 0
        return False

    def update(self, all_sprites):
        # ── Stun freeze ──
        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        self.animation_state()

        # ── If dying, play death and return ──
        if self.dying:
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Walk until attack range, then stop and attack ──
        if self.rect.y >= self.attack_range:
            self.set_state('attack')
            self.vel_x = 0
            self.vel_y = 0
        elif self.rect.y < self.attack_range - 50 and self.state != 'attack':
            self.set_state('walk')

        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        center = self.rect.center
        frame  = self.get_current_frame()
        self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
        self.rect  = self.image.get_rect(center=center)

        self.separate(all_sprites)

        if self.rect.left  < 0:             self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH:  self.rect.right = WINDOW_WIDTH
        if self.rect.top   > WINDOW_HEIGHT: self.kill()

    def health_bar(self, surface):
        """Draws a big health bar at the top of the screen with the boss name and HP numbers."""
        bar_w = 600
        bar_h = 24
        bar_x = WINDOW_WIDTH  // 2 - bar_w // 2   # Center the bar horizontally
        bar_y = 130

        fill = max(0, int(bar_w * (self.hp / self.max_hp)))   # How many pixels to fill

        # Change bar color based on remaining HP percentage
        if self.hp / self.max_hp > 0.5:
            bar_color = (0, 255, 0)     # Green: > 50% HP
        elif self.hp / self.max_hp > 0.25:
            bar_color = (255, 255, 0)   # Yellow: 25%–50% HP
        else:
            bar_color = (255, 0, 0)     # Red: < 25% HP

        pygame.draw.rect(surface, (30, 10, 40),    (bar_x, bar_y, bar_w, bar_h), border_radius=6)  # Dark background
        pygame.draw.rect(surface, bar_color,        (bar_x, bar_y, fill,  bar_h), border_radius=6)  # Filled portion
        pygame.draw.rect(surface, (200, 100, 255),  (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)  # Purple border

        label   = small_font.render("MINOTAUR", True, (200, 100, 255))
        surface.blit(label, (WINDOW_WIDTH // 2 - label.get_width() // 2, bar_y - 22))   # Name above bar

        hp_txt  = small_font.render(f"{self.hp} / {self.max_hp}", True, (220, 180, 255))
        surface.blit(hp_txt, (WINDOW_WIDTH // 2 - hp_txt.get_width() // 2, bar_y + 3))  # HP numbers inside bar

    def draw(self, surface):
        """Draw the Minotaur and its health bar (but not the health bar while dying)."""
        surface.blit(self.image, self.rect)
        if not self.dying:
            self.health_bar(surface)   # Hide health bar once death animation starts


# =============================================================
#  DRAGON CLASS  (Mini-boss — Medium mode)
# =============================================================
class Dragon(pygame.sprite.Sprite):
    """
    Medium difficulty mini-boss. Has 3 different attacks that cycle.
    Otherwise similar structure to Minotaur.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        self.animation = {
            'walk':          dragon_walking_frames,
            'first_attack':  dragon_first_attack_frames,
            'second_attack': dragon_second_attack,
            'third_attack':  dragon_third_attack_frames,
            'death':         dragon_death_frames
        }
        self.state    = 'walk'
        self.index    = 0.0
        self.image    = self.animation['walk'][0]
        self.rect     = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -50

        self.speed      = speed
        self.hp         = hp
        self.max_hp     = hp
        self.display_hp = hp
        self.dying      = False
        self.spawning   = True

        self.base_size    = 200
        self.max_size     = 1000
        self.current_size = self.base_size

        self.attack_range = WINDOW_HEIGHT * 0.36

        self.attack_timer  = 0
        self.delay_attack  = 350   # Dragon attacks very slowly
        self.damage_dealt  = False
        self.attack_cycle  = 0     # Tracks which attack to use next (cycles 0→1→2→0→...)

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        self.target_x = WINDOW_WIDTH  // 2
        self.target_y = WINDOW_HEIGHT + 100

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        """Each attack plays at a different speed. After an attack ends, cycle to next."""
        speeds = {
            'walk':          0.08,
            'first_attack':  0.015,   # Very slow — dramatic first attack
            'second_attack': 0.02,
            'third_attack':  0.02,
            'death':         0.08
        }
        speed  = speeds.get(self.state, 0.05)
        frames = self.animation[self.state]
        self.index += speed

        if self.index >= len(frames):
            if self.state == 'death':
                self.kill()
                return
            elif self.state in ('first_attack', 'second_attack', 'third_attack'):
                self.next_attack()   # Move to the next attack in the cycle
            else:
                self.index = 0.0

    def get_current_frame(self):
        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)
        return frames[safe_index]

    def take_hit(self):
        """Reduces HP. Triggers death at 0."""
        self.hp -= 1
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.set_state('death')
            self.vel_x = 0
            self.vel_y = 0

    def dealt_damage(self):
        """Returns True once per attack cycle. Does NOT deal damage during hit stun."""
        if self.hit_stun > 0:
            return False   # Can't deal damage while stunned

        attacking_state = {'first_attack', 'second_attack', 'third_attack'}
        if self.state in attacking_state and not self.dying:
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:
                self.attack_timer = 0
                return True
        else:
            self.attack_timer = 0
        return False

    def next_attack(self):
        """Cycle to the next attack pattern (first → second → third → first → ...)"""
        attacks = ['first_attack', 'second_attack', 'third_attack']
        self.attack_cycle = (self.attack_cycle + 1) % len(attacks)   # Modulo wraps back to 0
        self.set_state(attacks[self.attack_cycle])

    def update(self, all_sprites):
        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        self.animation_state()

        if self.dying:
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)
            return

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Switch to attack when in range, stay in attack once started ──
        if self.rect.y >= self.attack_range:
            if self.state not in ('first_attack', 'second_attack', 'third_attack'):
                self.set_state('first_attack')
            self.vel_x = 0
            self.vel_y = 0
        elif self.rect.y < self.attack_range - 50 and self.state not in ('first_attack', 'second_attack', 'third_attack'):
            self.set_state('walk')

        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        center = self.rect.center
        frame  = self.get_current_frame()
        self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
        self.rect  = self.image.get_rect(center=center)

        if self.rect.left  < 0:             self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH:  self.rect.right = WINDOW_WIDTH
        if self.rect.top   > WINDOW_HEIGHT: self.kill()

    def health_bar(self, surface):
        """Same health bar style as Minotaur, but labeled 'DRAGON'."""
        bar_w = 600
        bar_h = 24
        bar_x = WINDOW_WIDTH // 2 - bar_w // 2
        bar_y = 130
        fill  = max(0, int(bar_w * (self.hp / self.max_hp)))

        bar_color = (0, 255, 0) if self.hp / self.max_hp > 0.5 else \
                    (255, 255, 0) if self.hp / self.max_hp > 0.25 else (255, 0, 0)

        pygame.draw.rect(surface, (30, 10, 40),   (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, bar_color,       (bar_x, bar_y, fill,  bar_h), border_radius=6)
        pygame.draw.rect(surface, (200, 100, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)

        label  = small_font.render("DRAGON", True, (200, 100, 255))
        surface.blit(label,  (WINDOW_WIDTH // 2 - label.get_width() // 2,  bar_y - 22))

        hp_txt = small_font.render(f"{self.hp} / {self.max_hp}", True, (220, 180, 255))
        surface.blit(hp_txt, (WINDOW_WIDTH // 2 - hp_txt.get_width() // 2, bar_y + 3))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if not self.dying:
            self.health_bar(surface)


# =============================================================
#  SCIENTIST CLASS  (Mini-boss — Hard mode)
# =============================================================
class Scientist(pygame.sprite.Sprite):
    """
    The Hard difficulty mini-boss. Unlike Minotaur/Dragon, the Scientist
    has NO walk animation — it appears and immediately starts attacking.
    Also cycles through 3 attack patterns.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        self.animation = {
            'first_attack':  scientist_first_attack,
            'second_attack': scientist_second_attack,
            'third_attack':  scientist_third_attack,
            'death':         scientist_death_frames
        }
        self.state    = 'first_attack'   # Start attacking immediately (no walk animation)
        self.index    = 0.0
        self.image    = self.animation['first_attack'][0]
        self.rect     = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -50

        self.speed      = speed
        self.hp         = hp
        self.max_hp     = hp
        self.display_hp = hp
        self.dying      = False
        self.spawning   = True
        self.positioned = False   # True once it reaches its attack position

        self.base_size    = 200
        self.max_size     = 1000
        self.current_size = self.base_size

        self.attack_range = WINDOW_HEIGHT * 0.36

        self.attack_timer  = 0
        self.delay_attack  = 350
        self.damage_dealt  = False
        self.attack_cycle  = 0

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        # Target is exactly at attack_range height (not the bottom)
        self.target_x = WINDOW_WIDTH // 2
        self.target_y = int(self.attack_range)

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        speeds = {
            'first_attack':  0.02,
            'second_attack': 0.025,
            'third_attack':  0.02,
            'death':         0.08
        }
        speed  = speeds.get(self.state, 0.05)
        frames = self.animation[self.state]
        self.index += speed

        if self.index >= len(frames):
            if self.state == 'death':
                self.kill()
                return
            elif self.state in ('first_attack', 'second_attack', 'third_attack'):
                self.next_attack()
            else:
                self.index = 0.0

    def get_current_frame(self):
        frames     = self.animation[self.state]
        safe_index = min(int(self.index), len(frames) - 1)
        return frames[safe_index]

    def take_hit(self):
        """Reduces HP, applies hit stun, and triggers death if HP is 0."""
        self.hp       -= 1
        self.hit_stun  = self.HIT_STUN_TIME
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.set_state('death')
            self.vel_x = 0
            self.vel_y = 0

    def dealt_damage(self):
        """Returns True once per attack cycle, but ONLY after it has reached its position."""
        if self.hit_stun > 0:
            return False

        attacking_state = {'first_attack', 'second_attack', 'third_attack'}
        if self.state in attacking_state and self.positioned:
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:
                self.attack_timer = 0
                return True
        else:
            if not self.positioned:
                self.attack_timer = 0
        return False

    def next_attack(self):
        attacks = ['first_attack', 'second_attack', 'third_attack']
        self.attack_cycle = (self.attack_cycle + 1) % len(attacks)
        self.set_state(attacks[self.attack_cycle])

    def update(self, all_sprites):
        def scale_sprite():
            """Inner helper — scales the sprite based on screen position."""
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)

        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            scale_sprite()
            return

        self.animation_state()

        if self.dying:
            scale_sprite()
            return

        # ── Move down until reaching attack_range ──
        if not self.positioned:
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y

            if self.rect.centery >= self.attack_range:
                self.rect.center = (self.target_x, int(self.attack_range))   # Snap into exact position
                self.vel_x       = 0
                self.vel_y       = 0
                self.positioned  = True

        # ── Lock position once in place ──
        if self.positioned:
            locked_y = int(self.attack_range)
            scale_sprite()
            self.rect.centery = locked_y   # Force Y position every frame so it can't drift
            return

        scale_sprite()

        if self.rect.left  < 0:             self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH:  self.rect.right = WINDOW_WIDTH
        if self.rect.top   > WINDOW_HEIGHT: self.kill()

    def health_bar(self, surface):
        """Identical health bar style, labeled 'SCIENTIST'."""
        bar_w = 600
        bar_h = 24
        bar_x = WINDOW_WIDTH // 2 - bar_w // 2
        bar_y = 130
        fill  = max(0, int(bar_w * (self.hp / self.max_hp)))

        bar_color = (0, 255, 0) if self.hp / self.max_hp > 0.5 else \
                    (255, 255, 0) if self.hp / self.max_hp > 0.25 else (255, 0, 0)

        pygame.draw.rect(surface, (30, 10, 40),   (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, bar_color,       (bar_x, bar_y, fill,  bar_h), border_radius=6)
        pygame.draw.rect(surface, (200, 100, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)

        label  = small_font.render("SCIENTIST", True, (200, 100, 255))
        surface.blit(label,  (WINDOW_WIDTH // 2 - label.get_width()  // 2, bar_y - 22))
        hp_txt = small_font.render(f"{self.hp} / {self.max_hp}", True, (220, 180, 255))
        surface.blit(hp_txt, (WINDOW_WIDTH // 2 - hp_txt.get_width() // 2, bar_y + 3))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if not self.dying:
            self.health_bar(surface)


# =============================================================
#  DEMON LORD CLASS  (Final Boss — all modes)
# =============================================================
class DemonLord(pygame.sprite.Sprite):
    """
    The final boss. Has a two-phase fight:
      Phase 1: Uses 'first_attack' repeatedly until HP drops to 50%.
      Transformation: Plays a transformation animation at 50% HP.
      Phase 2: Cycles through 'second', 'third', and 'fourth' attacks.
    
    Dying while in transformation locks HP at 1 so it survives to finish transforming.
    """

    def __init__(self, speed, hp, spawn_x):
        super().__init__()
        self.animations = {
            'walk':           dl_walking,
            'idle':           dl_idle_frames,
            'first_attack':   dl_first_attack,
            'transformation': dl_transformation,
            'second_attack':  dl_second_attack_frames,
            'third_attack':   dl_third_attack_frames,
            'fourth_attack':  dl_fourth_attack_frames,
            'death':          dl_death_frames,
        }
        self.state    = 'walk'
        self.index    = 0.0
        self.image    = self.animations['walk'][0]
        self.rect     = self.image.get_rect()

        self.rect.centerx = spawn_x
        self.rect.y       = -100

        self.speed       = speed
        self.hp          = hp
        self.max_hp      = hp
        self.display_hp  = float(hp)   # Float for potential smooth HP bar animation
        self.dying       = False
        self.transformed = False        # Has the transformation happened yet?

        self.base_size    = 300   # Starts larger than regular enemies
        self.max_size     = 1000
        self.current_size = self.base_size

        self.attack_range = WINDOW_HEIGHT * 0.30   # Stops higher up than mini-bosses

        self.attack_timer  = 0
        self.delay_attack  = 120   # Attacks frequently
        self.damage_dealt  = False
        self.attack_cycle  = 0

        self.hit_stun      = 0
        self.HIT_STUN_TIME = 15

        self.target_x = WINDOW_WIDTH  // 2
        self.target_y = WINDOW_HEIGHT + 100
        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.index = 0.0

    def animation_state(self):
        """
        Complex state machine — handles looping, cycling, and transformation trigger.
        After first_attack ends: check if HP is low enough to transform.
        After transformation: enter phase 2 attacks.
        Phase 2 attacks cycle: second → third → fourth → second → ...
        """
        speeds = {
            'walk':           0.12,
            'idle':           0.08,
            'first_attack':   0.10,
            'transformation': 0.06,   # Transformation is slow and dramatic
            'second_attack':  0.10,
            'third_attack':   0.10,
            'fourth_attack':  0.10,
            'death':          0.08,
        }
        speed  = speeds.get(self.state, 0.1)
        frames = self.animations[self.state]
        self.index += speed

        if self.index >= len(frames):
            if self.state == 'death':
                self.kill()
                return
            elif self.state == 'first_attack':
                # After first attack, check if we should transform
                if not self.transformed and self.hp <= self.max_hp // 2:
                    self.set_state('transformation')
                else:
                    self.index = 0.0   # Loop first attack if HP is still high
            elif self.state == 'transformation':
                self.transformed = True          # Mark transformation as done
                self.set_state('second_attack')  # Enter phase 2
            elif self.state in ('second_attack', 'third_attack', 'fourth_attack'):
                self.next_attack()
            else:
                self.index = 0.0

    def get_current_frame(self):
        frames     = self.animations[self.state]
        safe_index = min(int(self.index), len(frames) - 1)
        return frames[safe_index]

    def take_hit(self, damage=1):
        """
        Complex hit logic:
        - Ignore hits while already dying.
        - Force transformation at 50% HP — keep HP at 1 so it survives.
        - After transformation, allow death at 0 HP.
        """
        if self.dying:
            return   # Already dead — ignore further hits

        self.hp -= damage

        # ── Force transformation if HP crosses 50% threshold ──
        if self.hp <= self.max_hp // 2 and not self.transformed:
            self.transformed = False   # Will be set True when anim finishes
            if self.state not in ('transformation', 'death'):
                self.hp = max(1, self.hp)   # Clamp to 1 HP so it survives to transform
                self.set_state('transformation')
                self.vel_x = 0
                self.vel_y = 0
                return

        # ── Death check (only triggers after transformation is done) ──
        if self.hp <= 0 and not self.dying:
            self.dying    = True
            self.vel_x    = 0
            self.vel_y    = 0
            self.hit_stun = 0   # Clear stun so death animation plays immediately
            self.set_state('death')
            return

        # ── Normal hit stun ──
        self.hit_stun     = self.HIT_STUN_TIME
        self.vel_x        = 0
        self.vel_y        = 0
        self.attack_timer = 0

    def dealt_damage(self):
        """Returns True once per attack cycle. Never during stun or while dying."""
        if self.hit_stun > 0 or self.dying:
            return False

        attacking_state = {'first_attack', 'second_attack', 'third_attack', 'fourth_attack'}
        if self.state == 'first_attack' or (self.transformed and self.state in attacking_state):
            self.attack_timer += 1
            if self.attack_timer >= self.delay_attack:
                self.attack_timer = 0
                return True
        else:
            self.attack_timer = 0
        return False

    def next_attack(self):
        """Cycle through phase 2 attacks."""
        attacks = ['second_attack', 'third_attack', 'fourth_attack']
        self.attack_cycle = (self.attack_cycle + 1) % len(attacks)
        self.set_state(attacks[self.attack_cycle])

    def update(self, all_sprites):
        def scale_sprite():
            """Scale sprite based on vertical progress down the screen."""
            progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
            self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)
            center = self.rect.center
            frame  = self.get_current_frame()
            self.image = pygame.transform.scale(frame, (self.current_size, self.current_size))
            self.rect  = self.image.get_rect(center=center)

        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.animation_state()
            scale_sprite()
            return

        if self.dying:
            self.animation_state()
            scale_sprite()
            return

        self.animation_state()

        if self.rect.y >= self.attack_range:
            # ── Stop and choose the right attack phase ──
            self.vel_x = 0
            self.vel_y = 0
            if not self.transformed:
                if self.state not in ('first_attack', 'transformation'):
                    self.set_state('first_attack')
            else:
                if self.state not in ('second_attack', 'third_attack',
                                      'fourth_attack', 'transformation'):
                    self.set_state('second_attack')
        else:
            # ── Still walking down — keep moving ──
            if self.state not in ('first_attack', 'transformation',
                                  'second_attack', 'third_attack', 'fourth_attack'):
                self.set_state('walk')
            self.vel_x, self.vel_y = self.get_velocity()
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y

        scale_sprite()

        if self.rect.left  < 0:             self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH:  self.rect.right = WINDOW_WIDTH
        if self.rect.top   > WINDOW_HEIGHT: self.kill()

    def health_bar(self, surface):
        """Labeled 'DEMON LORD'. Same structure as other boss health bars."""
        bar_w = 600
        bar_h = 24
        bar_x = WINDOW_WIDTH // 2 - bar_w // 2
        bar_y = 130
        fill  = max(0, int(bar_w * (self.hp / self.max_hp)))

        bar_color = (0, 255, 0) if self.hp / self.max_hp > 0.5 else \
                    (255, 255, 0) if self.hp / self.max_hp > 0.25 else (255, 0, 0)

        pygame.draw.rect(surface, (30, 10, 40),   (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, bar_color,       (bar_x, bar_y, fill,  bar_h), border_radius=6)
        pygame.draw.rect(surface, (200, 100, 255), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)

        label  = small_font.render("DEMON LORD", True, (200, 100, 255))
        surface.blit(label,  (WINDOW_WIDTH // 2 - label.get_width()  // 2, bar_y - 22))
        hp_txt = small_font.render(f"{self.hp} / {self.max_hp}", True, (220, 180, 255))
        surface.blit(hp_txt, (WINDOW_WIDTH // 2 - hp_txt.get_width() // 2, bar_y + 3))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if not self.dying:
            self.health_bar(surface)


# =============================================================
#  CIVILIAN CLASS
# =============================================================
class Civilian(pygame.sprite.Sprite):
    """
    NPCs that run across the screen alongside enemies.
    - Shooting a civilian costs you 1 HP (penalty!).
    - If a civilian reaches the bottom safely, you gain 1 HP (reward!).
    - Randomly male or female.
    """

    def __init__(self, enemies):
        super().__init__()
        self.gender    = random.choice(['male', 'female'])   # Randomly pick gender
        self.run_frames  = CIVILIAN_TYPE[self.gender]['run']   # Look up their run animation
        self.dead_frames = CIVILIAN_TYPE[self.gender]['dead']  # And their death animation

        self.animation = self.run_frames
        self.index     = 0.0
        self.image     = self.animation[0]
        self.rect      = self.image.get_rect()

        self.rect.x = random.randint(100, WINDOW_WIDTH - 100)
        self.rect.y = -80   # Start above screen

        self.direction = random.choice([-1, 1])   # -1 = running left, 1 = running right
        self.speed     = 3
        self.hp        = 1
        self.dying     = False
        self.spawning  = True
        self.escaped   = False

        self.base_size    = 120
        self.max_size     = 300
        self.current_size = self.base_size

        # ── Spawn near a random existing enemy if any exist ──
        if enemies:
            enemy = random.choice(enemies)
            # Appear just ahead of (below) the enemy, with a small random offset
            self.rect.centerx = enemy.rect.centerx + random.randint(-60, 60)
            self.rect.y       = enemy.rect.y + enemy.current_size
        else:
            # No enemies yet — just pick a random top position
            self.rect.centerx = random.randint(100, WINDOW_WIDTH - 100)
            self.rect.y       = -80

        # Clamp so the civilian doesn't spawn off the sides of the screen
        self.rect.centerx = max(60, min(WINDOW_WIDTH - 60, self.rect.centerx))

        self.target_x = WINDOW_WIDTH  // 2
        self.target_y = WINDOW_HEIGHT + 100

        self.vel_x, self.vel_y = self.get_velocity()

    def get_velocity(self):
        """Same vector math as enemies — civilians run toward the center-bottom."""
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        if distance != 0:
            vel_x = (dx / distance) * self.speed
            vel_y = (dy / distance) * self.speed
        else:
            vel_x = 0
            vel_y = 0
        return vel_x, vel_y

    def separate(self, all_sprites):
        """Push away from overlapping sprites (same as enemies)."""
        for other in all_sprites:
            if other is self:
                continue
            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            min_dist = (self.current_size + other.current_size) // 2
            if 0 < distance < min_dist:
                overlap = min_dist - distance
                self.rect.x += int((dx / distance) * overlap * 0.5)
                self.rect.y += int((dy / distance) * overlap * 0.5)

    def animation_state(self):
        """Plays death animation once-through then removes the sprite; run animation loops."""
        if self.dying:
            self.index += 0.1
            if self.index >= len(self.dead_frames):
                self.kill()   # Remove after death animation finishes
                return
            self.image = self.dead_frames[int(self.index)]
        else:
            self.index += 0.2   # Run animation is faster than most enemies
            if self.index >= len(self.animation):
                self.index = 0.0
            self.image = self.animation[int(self.index)]

    def die(self):
        """Called when the player accidentally shoots a civilian."""
        if not self.dying:
            self.dying = True
            self.index = 0.0   # Start death from first frame
            self.vel_x = 0
            self.vel_y = 0     # Stop moving

    def update(self, enemies, all_sprites):
        """Update movement, scaling, and check if escaped."""
        if self.dying:
            self.animation_state()
            return   # Once dying, stop all movement logic

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Scale bigger as they move down ──
        progress = max(0, min(1, self.rect.y / WINDOW_HEIGHT))
        self.current_size = int(self.base_size + (self.max_size - self.base_size) * progress)

        center     = self.rect.center
        self.image = pygame.transform.scale(
            self.animation[int(self.index)],
            (self.current_size, self.current_size)
        )
        self.rect  = self.image.get_rect(center=center)

        self.separate(all_sprites)

        if self.rect.left  < 0:            self.rect.left  = 0
        if self.rect.right > WINDOW_WIDTH: self.rect.right = WINDOW_WIDTH

        # ── If civilian reaches the bottom edge, they "escaped" — player gets healed ──
        if self.rect.top > WINDOW_HEIGHT:
            self.escaped = True
            self.kill()

        self.animation_state()

    def draw(self, screen):
        """Draw the civilian, flipping the image if running left."""
        if self.vel_x < 0:
            flipped = pygame.transform.flip(self.image, True, False)   # Flip horizontally
            screen.blit(flipped, self.rect)
        else:
            screen.blit(self.image, self.rect)


# =============================================================
#  BULLET CLASS
# =============================================================
class Bullet:
    """
    A single projectile fired by the player.
    Travels toward the mouse click position and disappears when it arrives.
    """

    def __init__(self, start_x, start_y, target_x, target_y):
        self.image  = bullet_image
        self.rect   = pygame.Rect(start_x, start_y, 8, 8)   # Small 8x8 collision box
        self.speed  = 10
        self.alive  = True   # Set to False to mark for removal

        # ── Calculate direction from spawn to mouse click ──
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.sqrt(dx**2 + dy**2)

        if distance != 0:
            self.vel_x = (dx / distance) * self.speed
            self.vel_y = (dy / distance) * self.speed
        else:
            self.vel_x = 0
            self.vel_y = 0

        # Remember the target to know when to stop
        self.target_x = target_x
        self.target_y = target_y

    def update(self):
        """Move the bullet and check if it has reached its target."""
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # ── Stop when the bullet reaches the click point ──
        dx = self.target_x - self.rect.centerx
        dy = self.target_y - self.rect.centery
        distance_to_target = math.sqrt(dx**2 + dy**2)

        if distance_to_target < 10:   # Within 10 pixels = "close enough"
            self.alive = False

    def draw(self, screen):
        """Draw the bullet as a small yellow rounded rectangle."""
        pygame.draw.rect(screen, (255, 220, 0), self.rect, border_radius=3)


# =============================================================
#  AIM / CROSSHAIR CLASS
# =============================================================
class Aim(pygame.sprite.Sprite):
    """
    A custom crosshair image that follows the mouse.
    This replaces the OS cursor (which we hid at the start).
    """

    def __init__(self, *groups):
        super().__init__(*groups)
        self.image = pygame.image.load('image/aim.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect  = self.image.get_rect()

    def update(self):
        """Move the aim image to wherever the mouse currently is."""
        mouse_x, mouse_y   = pygame.mouse.get_pos()
        self.rect.center   = (mouse_x, mouse_y)


# =============================================================
#  HUD HELPER FUNCTIONS
# =============================================================

def draw_ammo(surface, ammo, max_ammo=6):
    """
    Draws the ammo indicator in the bottom-left corner.
    Filled bullets = remaining ammo. Dim bullets = empty slots.
    """
    ammo_img  = pygame.transform.scale(bullet_image, (30, 15))    # Full-opacity bullet icon
    empty_img = pygame.transform.scale(bullet_image, (30, 15))    # Same image, but dimmed
    empty_img.set_alpha(60)   # 60/255 opacity = semi-transparent "empty" slots

    for i in range(max_ammo):
        x = 20 + i * 40    # Each bullet is spaced 40 pixels apart
        y = WINDOW_HEIGHT - 50
        if i < ammo:
            surface.blit(ammo_img,  (x, y))   # Still have this bullet
        else:
            surface.blit(empty_img, (x, y))   # This bullet has been spent


def draw_button(surface, text, rect, color, hovered, fnt):
    """
    Draws a clickable button with a glow effect when hovered.
    
    surface  — the pygame surface to draw on
    text     — label text shown on the button
    rect     — a pygame.Rect defining the button's position and size
    color    — the button's accent color (border/glow/fill)
    hovered  — True if the mouse is over the button right now
    fnt      — the font to render the label in
    """
    # ── Glow halo behind the button when hovered ──
    if hovered:
        glow = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        glow.fill((*color, 55))   # Semi-transparent glow matching the button color
        surface.blit(glow, (rect.x - 10, rect.y - 10))

    # ── Button background ──
    pygame.draw.rect(surface, (15, 15, 25), rect, border_radius=12)   # Dark fill

    # ── Border or filled background depending on hover state ──
    border_width = 0 if hovered else 3   # 0 = solid fill when hovered, 3px border otherwise
    pygame.draw.rect(surface, color, rect, width=border_width, border_radius=12)

    if hovered:
        # ── Add a semi-transparent color overlay when hovered ──
        pygame.draw.rect(surface, (*color, 160), rect, border_radius=12)

    # ── Centered text label ──
    txt = fnt.render(text, True, (255, 255, 255))
    surface.blit(txt, (rect.centerx - txt.get_width() // 2,
                        rect.centery - txt.get_height() // 2))


def get_head_rect(sprite):
    """
    Returns a rectangle covering the top 30% of a sprite's rect.
    Used for headshot detection — bullets hitting the head deal double damage.
    """
    head_height = int(sprite.rect.height * 0.3)   # Top 30% of the sprite = head zone
    return pygame.Rect(
        sprite.rect.x,
        sprite.rect.y,
        sprite.rect.width,
        head_height
    )


# =============================================================
#  SCREEN FUNCTIONS
# =============================================================

def main_menu():
    """
    Shows the main menu with PLAY and QUIT buttons.
    Returns 'play' when the player clicks PLAY.
    """
    pygame.mouse.set_visible(True)   # Show mouse cursor on menu screens
    tick = 0

    while True:
        tick += 1
        mx, my = pygame.mouse.get_pos()

        # ── Draw background and dark overlay ──
        window_screen.blit(scaled_mainBG, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))   # 120/255 = ~47% opacity dark overlay
        window_screen.blit(overlay, (0, 0))

        # ── Pulsing title — brightness oscillates using sine wave ──
        pulse = abs(math.sin(tick * 0.03)) * 10   # Slow, gentle pulse
        title_color = (255, int(50 + pulse * 2), int(50 + pulse * 2))   # Red that shifts toward pink
        title = big_font.render("INVENTION OUTBREAK", True, title_color)
        window_screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        sub = small_font.render("survive the monster horde", True, (200, 180, 180))
        window_screen.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 175))

        # ── Button rectangles ──
        play_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 260, 300, 70)
        quit_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 360, 300, 70)

        play_hov = play_rect.collidepoint(mx, my)   # Is the mouse over the PLAY button?
        quit_hov = quit_rect.collidepoint(mx, my)

        draw_button(window_screen, "PLAY", play_rect, (80, 200, 80),  play_hov, pixel_font)
        draw_button(window_screen, "QUIT", quit_rect, (200, 60, 60),  quit_hov, pixel_font)

        # ── Controls hint at the bottom ──
        hint = small_font.render(
            "left click to shoot  |  R to reload  |  aim with mouse",
            True, (160, 140, 140))
        window_screen.blit(hint, (WINDOW_WIDTH // 2 - hint.get_width() // 2, WINDOW_HEIGHT - 50))

        # ── Event loop ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()   # Close everything cleanly
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_rect.collidepoint(mx, my):
                    return 'play'
                if quit_rect.collidepoint(mx, my):
                    pygame.quit(); exit()

        pygame.display.update()
        clock.tick(60)   # Cap at 60 frames per second


def difficulty_screen():
    """
    Shows the difficulty selection screen.
    Returns the chosen difficulty label ('Easy', 'Medium', 'Hard'),
    or None if the player goes back.
    """
    pygame.mouse.set_visible(True)
    hovered = None

    while True:
        mx, my = pygame.mouse.get_pos()

        window_screen.blit(scaled_mainBG, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        window_screen.blit(overlay, (0, 0))

        title = big_font.render("SELECT DIFFICULTY", True, (255, 60, 60))
        window_screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 60))

        sub = small_font.render("choose your challenge", True, (200, 180, 180))
        window_screen.blit(sub, (WINDOW_WIDTH // 2 - sub.get_width() // 2, 155))

        buttons = {}   # Will map difficulty label → rect for click detection
        labels  = ['Easy', 'Medium', 'Hard']

        for i, label in enumerate(labels):
            color = LEVELS[label]['color']   # Each difficulty has its own color
            bx, by = WINDOW_WIDTH // 2 - 280, 220 + i * 140
            bw, bh = 560, 100
            rect = pygame.Rect(bx, by, bw, bh)
            hov  = rect.collidepoint(mx, my)

            # ── Glow ──
            if hov:
                glow = pygame.Surface((bw + 20, bh + 20), pygame.SRCALPHA)
                glow.fill((*color, 55))
                window_screen.blit(glow, (bx - 10, by - 10))

            # ── Button body ──
            pygame.draw.rect(window_screen, (15, 15, 25), rect, border_radius=12)
            pygame.draw.rect(window_screen, color, rect, width=0 if hov else 3, border_radius=12)
            if hov:
                s = pygame.Surface((bw, bh), pygame.SRCALPHA)
                s.fill((*color, 60))
                window_screen.blit(s, (bx, by))

            # ── Label (e.g. "EASY") ──
            lbl = pixel_font.render(label.upper(), True, (255, 255, 255))
            window_screen.blit(lbl, (WINDOW_WIDTH // 2 - lbl.get_width() // 2, by + 12))

            # ── Description line (e.g. "Slow spawn | 6 ammo | Fast reload") ──
            desc = small_font.render(LEVELS[label]['description'], True, (200, 200, 200))
            window_screen.blit(desc, (WINDOW_WIDTH // 2 - desc.get_width() // 2, by + 58))

            buttons[label] = rect

        # ── Back button (returns to main menu) ──
        back_rect = pygame.Rect(30, 30, 120, 50)
        back_hov  = back_rect.collidepoint(mx, my)
        draw_button(window_screen, "BACK", back_rect, (120, 120, 200), back_hov, small_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mx, my):
                    return None   # None signals "go back to main menu"
                for label, rect in buttons.items():
                    if rect.collidepoint(mx, my):
                        pygame.mouse.set_visible(False)   # Hide cursor before entering game
                        return label

        pygame.display.update()
        clock.tick(60)


def result_screen(title_text, title_color, score):
    """
    Shows the win/lose screen with the player's score.
    Returns 'retry' to play again with the same settings,
    or 'menu' to return to the main menu.
    """
    pygame.mouse.set_visible(True)

    while True:
        mx, my = pygame.mouse.get_pos()

        window_screen.blit(scaled_mainBG, (0, 0))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))   # Slightly darker overlay for result screen
        window_screen.blit(overlay, (0, 0))

        title = big_font.render(title_text, True, title_color)
        window_screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 150))

        score_txt = pixel_font.render(f"score: {score}", True, (255, 220, 0))
        window_screen.blit(score_txt, (WINDOW_WIDTH // 2 - score_txt.get_width() // 2, 280))

        retry_rect = pygame.Rect(WINDOW_WIDTH // 2 - 240, 380, 210, 65)
        menu_rect  = pygame.Rect(WINDOW_WIDTH // 2 + 30,  380, 210, 65)

        draw_button(window_screen, "RETRY", retry_rect, (80, 200, 80),  retry_rect.collidepoint(mx, my), pixel_font)
        draw_button(window_screen, "MENU",  menu_rect,  (80, 120, 200), menu_rect.collidepoint(mx, my),  pixel_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if retry_rect.collidepoint(mx, my):
                    pygame.mouse.set_visible(False)
                    return 'retry'
                if menu_rect.collidepoint(mx, my):
                    return 'menu'

        pygame.display.update()
        clock.tick(60)


# =============================================================
#  MAIN GAME LOOP
# =============================================================
def run_game(settings):
    """
    The core gameplay function. Runs until the player wins or loses.
    Returns (score, 'win') or (score, 'lose').
    
    settings — the difficulty dictionary from LEVELS, with 'label' added.
    """

    # ── Shooting state ──
    bullets        = []              # List of all active Bullet objects
    shoot_cooldown = 0               # Frames remaining before we can shoot again
    SHOOT_DELAY    = settings['shoot_delay']
    MAX_AMMO       = settings['max_ammo']
    ammo           = MAX_AMMO

    # ── Reload state ──
    Reload_time   = settings['reload_time']
    reload_timer  = 0
    reloading     = False

    # ── Enemy spawning ──
    spawn_timer    = 0
    spawn_interval = settings['spawn_interval']

    # ── Civilian spawning ──
    civilian_timer    = 0
    civilian_interval = 160   # Frames between civilian spawns

    score     = 0
    player_hp = 5   # Player starts with 5 HP

    damage_flash = 0   # Frames remaining for the red screen flash when taking damage

    # ── Wave system state ──
    enemies_spawned   = 0
    civilians_spawned = 0
    Max_Enemies       = settings['max_enemies']
    Max_Civilians     = settings['max_civilians']
    Enemies_Per_Wave  = settings['enemies_per_wave']

    wave_number              = 0      # Which wave we're on (starts at 0, increments before display)
    wave_in_progress         = False  # True while enemies are still alive this wave
    wave_timer               = 0      # Counts up between waves
    wave_delay               = 180    # Frames to wait between waves (180 = 3 seconds at 60fps)
    wave_label_timer         = 0      # Countdown for how long to show the "WAVE X" banner
    civilian_spawned_this_wave = False
    boss_spawned             = False  # Has the mini-boss appeared yet?
    Boss_wave                = 3      # Mini-boss appears on wave 3
    final_boss_spawned       = False
    final_boss_wave          = 5      # Demon Lord appears on wave 5
    boss_wave_active         = False
    boss_transition_timer    = 0
    BOSS_TRANSITION_TIME     = 120

    # ── Sprite groups — pygame uses these to manage collections of sprites ──
    slime_group      = pygame.sprite.Group()
    goblin_group     = pygame.sprite.Group()
    skeleton_group   = pygame.sprite.Group()
    civilian_group   = pygame.sprite.Group()
    mini_boss_group  = pygame.sprite.Group()   # One group for all mini-boss types
    final_boss_group = pygame.sprite.Group()
    aim_group        = pygame.sprite.GroupSingle()   # Only ever one aim crosshair
    aim_group.add(Aim())

    font = pygame.font.Font('Game Shark.otf', 28)

    # ── Inner function: spawn a new wave of enemies ──
    def spawn_wave():
        nonlocal enemies_spawned, wave_number, wave_in_progress
        nonlocal wave_label_timer, civilians_spawned, civilian_spawned_this_wave
        nonlocal boss_spawned, final_boss_spawned, boss_wave_active, boss_transition_timer
        # 'nonlocal' lets us modify variables from the outer function (run_game)

        wave_number   += 1
        wave_label_timer = 120   # Show the wave banner for 2 seconds (120 frames)
        civilian_spawned_this_wave = False

        # ── Wave 3: spawn the mini-boss (difficulty determines which one) ──
        if wave_number == Boss_wave and not boss_spawned:
            boss_x = 660   # Spawn at screen center-X

            if settings['label'] == 'Hard':
                mini_boss_group.add(Scientist(
                    speed=settings.get('scientist_speed', 1),
                    hp=settings.get('scientist_hp', 40),
                    spawn_x=boss_x
                ))
            elif settings['label'] == 'Medium':
                mini_boss_group.add(Dragon(
                    speed=settings.get('dragon_speed', 1),
                    hp=settings.get('dragon_hp', 40),
                    spawn_x=boss_x
                ))
            else:
                mini_boss_group.add(Minotaur(
                    speed=settings['minotaur_speed'],
                    hp=settings['minotaur_hp'],
                    spawn_x=boss_x
                ))

            boss_spawned     = True
            wave_label_timer = 180   # Extra long banner for boss wave
            wave_in_progress = True
            return

        # ── Wave 5: spawn the Demon Lord (final boss) ──
        if wave_number == final_boss_wave and not final_boss_spawned:
            final_boss_group.add(DemonLord(
                speed=settings['demon_lord_speed'],
                hp=settings['demon_lord_hp'],
                spawn_x=WINDOW_WIDTH // 2
            ))
            final_boss_spawned    = True
            wave_label_timer      = 200
            wave_in_progress      = True
            boss_wave_active      = True
            boss_transition_timer = BOSS_TRANSITION_TIME
            return

        # ── Regular waves: spawn a batch of random enemies ──
        to_spawn = min(Enemies_Per_Wave, Max_Enemies - enemies_spawned)
        if to_spawn <= 0:
            return   # No more enemies to spawn

        for _ in range(to_spawn):
            spawn_x      = get_spawn_x([slime_group, goblin_group, skeleton_group])
            monster_type = random.choice(['slime', 'goblin', 'skeleton'])

            if monster_type == 'slime':
                slime_group.add(Slime(speed=settings['slime_speed'], hp=settings['slime_hp'], spawn_x=spawn_x))
            elif monster_type == 'goblin':
                goblin_group.add(Goblin(speed=settings['goblin_speed'], hp=settings['goblin_hp'], spawn_x=spawn_x))
            elif monster_type == 'skeleton':
                skeleton_group.add(Skeleton(speed=settings['skeleton_speed'], hp=settings['skeleton_hp'], spawn_x=spawn_x))

            enemies_spawned += 1

        wave_in_progress = True

        # ── Spawn one civilian per wave, near a random enemy ──
        if civilians_spawned < Max_Civilians:
            enemies = list(slime_group) + list(goblin_group)
            if enemies:
                civilian_group.add(Civilian(enemies))
                civilians_spawned          += 1
                civilian_spawned_this_wave  = True

    spawn_wave()   # Start wave 1 immediately

    # ──────────────────────────────────────────────────────────
    #  MAIN GAME LOOP — runs 60 times per second
    # ──────────────────────────────────────────────────────────
    running = True
    while running:

        # ── Event handling — keyboard/mouse input ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Only shoot on left click, if cooldown expired, have ammo, and not reloading
                if shoot_cooldown <= 0 and ammo > 0 and not reloading:
                    if event.button == 1:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        bullet = Bullet(
                            start_x=aim_group.sprite.rect.centerx,
                            start_y=aim_group.sprite.rect.centery,
                            target_x=mouse_x,
                            target_y=mouse_y
                        )
                        bullets.append(bullet)
                        gun_shot_sound.play()
                        shoot_cooldown = SHOOT_DELAY
                        ammo -= 1

                        # Auto-reload when the last bullet is fired
                        if ammo <= 0:
                            reloading    = True
                            reload_timer = Reload_time
                            reload_sound.play()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and not reloading:   # R key = manual reload
                    reloading    = True
                    reload_timer = Reload_time
                    reload_sound.play()

        # ── Tick down all timers ──
        if shoot_cooldown > 0: shoot_cooldown -= 1
        if damage_flash   > 0: damage_flash   -= 1
        if wave_label_timer > 0: wave_label_timer -= 1

        # ── Reload countdown ──
        if reloading:
            reload_timer -= 1
            if reload_timer <= 0:
                ammo      = MAX_AMMO   # Refill ammo
                reloading = False

        # ── Spawn timer (currently not used to trigger spawns, waves are event-driven) ──
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            spawn_timer = 0

        # ── Check if the current wave is complete ──
        if wave_in_progress:
            if wave_number == final_boss_wave:
                if len(final_boss_group) == 0 and final_boss_spawned:
                    wave_in_progress = False
                    wave_timer       = 0
            elif wave_number == Boss_wave:
                if len(mini_boss_group) == 0 and boss_spawned:
                    wave_in_progress = False
                    wave_timer       = 0
            else:
                all_dead = (
                    len(slime_group)    == 0 and
                    len(goblin_group)   == 0 and
                    len(skeleton_group) == 0 and
                    enemies_spawned > 0
                )
                if all_dead:
                    wave_in_progress = False
                    wave_timer       = 0

        # ── Between waves: wait, then spawn the next wave ──
        if not wave_in_progress:
            regular_done    = enemies_spawned >= Max_Enemies
            boss_done       = not boss_spawned or len(mini_boss_group) == 0
            final_boss_done = not final_boss_spawned or len(final_boss_group) == 0

            if final_boss_done and final_boss_spawned:
                return score, 'win'   # ← Player beat the final boss — YOU WIN!

            if regular_done and boss_done and not final_boss_spawned:
                return score, 'win'

            if wave_number < final_boss_wave:
                wave_timer += 1
                if wave_timer >= wave_delay:
                    wave_timer = 0
                    spawn_wave()

        # ── Player takes damage if enemies reach the bottom ──
        for slime in list(slime_group):
            if slime.rect.top > WINDOW_HEIGHT:
                slime.kill()
                player_hp   -= 1
                damage_flash = 20

        for goblin in list(goblin_group):
            if goblin.rect.top > WINDOW_HEIGHT:
                goblin.kill()
                player_hp   -= 1
                damage_flash = 20

        for minotaur in list(mini_boss_group):
            if minotaur.rect.top > WINDOW_HEIGHT:
                minotaur.kill()
                player_hp   -= 1
                damage_flash = 20

        for dragon in list(mini_boss_group):
            if dragon.rect.top > WINDOW_HEIGHT:
                dragon.kill()
                player_hp   -= 1
                damage_flash = 20

        for demonLord in list(final_boss_group):
            if demonLord.rect.top > WINDOW_HEIGHT:
                demonLord.kill()
                player_hp   -= 1
                damage_flash = 20

        if player_hp <= 0:
            return score, 'lose'   # ← Player is dead — GAME OVER

        # ── Check if all enemies have been defeated and all waves done ──
        all_enemies_done = (
            enemies_spawned >= Max_Enemies and
            len(slime_group)      == 0 and
            len(goblin_group)     == 0 and
            len(skeleton_group)   == 0 and
            len(mini_boss_group)  == 0 and
            len(final_boss_group) == 0 and
            boss_spawned and
            final_boss_spawned and
            not wave_in_progress
        )
        if all_enemies_done:
            return score, 'win'

        # ── Build flat lists for collision and separation ──
        all_sprites = (list(slime_group) + list(goblin_group) + list(skeleton_group) +
                       list(civilian_group) + list(mini_boss_group) + list(final_boss_group))
        enemies = (list(slime_group) + list(goblin_group) + list(skeleton_group) +
                   list(mini_boss_group) + list(final_boss_group))

        # ── Update all sprites ──
        for slime in slime_group:
            slime.update(all_sprites)

        for goblin in goblin_group:
            goblin.update(all_sprites)
            if goblin.dealt_damage():   # Goblin attacks — subtract player HP
                player_hp   -= 1
                damage_flash = 20

        for skeleton in skeleton_group:
            skeleton.update(all_sprites)
            if skeleton.dealt_damage():
                player_hp   -= 1
                damage_flash = 20

        for minotaur in mini_boss_group:
            minotaur.update(all_sprites)
            if minotaur.dealt_damage():
                player_hp   -= 1
                damage_flash = 20

        for dragon in mini_boss_group:
            dragon.update(all_sprites)
            if dragon.dealt_damage():
                player_hp   -= 1
                damage_flash = 20

        for demonLord in final_boss_group:
            demonLord.update(all_sprites)
            if demonLord.dealt_damage():
                player_hp   -= 1
                damage_flash = 20

        for civilian in civilian_group:
            civilian.update(enemies, all_sprites)
            if civilian.escaped:            # Civilian made it to safety — heal the player
                player_hp       = min(player_hp + 1, 5)   # Heal 1, capped at 5
                civilian.escaped = False

        # ── DRAW EVERYTHING ────────────────────────────────────
        window_screen.blit(scaled_image, (0, 0))   # Draw the background first

        # ── Red flash overlay when taking damage ──
        if damage_flash > 0:
            flash = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 0, 0, 80))   # Semi-transparent red
            window_screen.blit(flash, (0, 0))

        # ── Draw all sprites (civilians behind enemies, enemies in front) ──
        for civilian  in civilian_group:   civilian.draw(window_screen)
        for slime     in slime_group:      slime.draw(window_screen)
        for goblin    in goblin_group:     goblin.draw(window_screen)
        for skeleton  in skeleton_group:   skeleton.draw(window_screen)
        for minotaur  in mini_boss_group:  minotaur.draw(window_screen)
        for demonLord in final_boss_group: demonLord.draw(window_screen)

        # ── Update and draw bullets, handle collisions ──
        to_remove = set()   # We collect bullets to remove AFTER iterating (safe to modify after loop)

        for bullet in bullets[:]:   # bullets[:] = a copy, so it's safe to iterate while modifying
            bullet.update()
            bullet.draw(window_screen)

            # ── Civilian hit check (highest priority — penalty for shooting civilians) ──
            civilian_hit = False
            for civilian in civilian_group:
                if bullet.rect.colliderect(civilian.rect):
                    civilian.die()
                    player_hp   -= 1
                    damage_flash = 20
                    to_remove.add(bullet)
                    civilian_hit = True
                    break
            if civilian_hit:
                continue   # Skip the enemy hit checks for this bullet

            # ── Slime hit check ──
            for slime in slime_group:
                if bullet.rect.colliderect(slime.rect):
                    head_rect = get_head_rect(slime)
                    damage    = 2 if bullet.rect.colliderect(head_rect) else 1   # Headshot = 2 damage
                    slime.hp -= damage
                    slime.hit_stun = slime.HIT_STUN_TIME
                    if slime.hp <= 0:
                        slime.kill()
                        score += 10
                    to_remove.add(bullet)
                    break

            # ── Goblin hit check ──
            for goblin in goblin_group:
                if bullet.rect.colliderect(goblin.rect):
                    head_rect = get_head_rect(goblin)
                    damage    = 2 if bullet.rect.colliderect(head_rect) else 1
                    goblin.hp -= damage
                    goblin.hit_stun = goblin.HIT_STUN_TIME
                    if goblin.hp <= 0:
                        goblin.kill()
                        score += 15
                    to_remove.add(bullet)
                    break

            # ── Skeleton hit check ──
            for skeleton in skeleton_group:
                if bullet.rect.colliderect(skeleton.rect):
                    head_rect = get_head_rect(skeleton)
                    damage    = 2 if bullet.rect.colliderect(head_rect) else 1
                    for _ in range(damage):
                        skeleton.take_hit()   # Skeleton uses take_hit() for death animation
                    if skeleton.hp <= 0:
                        score += 20
                    to_remove.add(bullet)
                    break

            # ── Mini-boss hit check ──
            for minotaur in mini_boss_group:
                if bullet.rect.colliderect(minotaur.rect):
                    head_rect = get_head_rect(minotaur)
                    if bullet.rect.colliderect(head_rect):
                        damage  = 2
                        score  += 2   # Bonus score for headshots on the boss
                    else:
                        damage  = 1
                    for _ in range(damage):
                        minotaur.take_hit()
                    if minotaur.hp <= 0:
                        score += 50
                    to_remove.add(bullet)
                    break

            # ── Final boss hit check ──
            for demonLord in final_boss_group:
                if bullet.rect.colliderect(demonLord.rect):
                    head_rect = get_head_rect(demonLord)
                    if bullet.rect.colliderect(head_rect):
                        damage  = 2
                        score  += 3   # Bigger bonus for headshots on the Demon Lord
                    else:
                        damage  = 1
                    demonLord.take_hit(damage)
                    if demonLord.hp <= 0:
                        score += 200
                    to_remove.add(bullet)
                    break

            # ── Remove bullet if it reached its target ──
            if not bullet.alive:
                to_remove.add(bullet)

            # ── Remove bullet if it left the screen ──
            if bullet.rect.x < 0 or bullet.rect.x > WINDOW_WIDTH:
                to_remove.add(bullet)
            if bullet.rect.y < 0 or bullet.rect.y > WINDOW_HEIGHT:
                to_remove.add(bullet)

        # ── Remove flagged bullets ──
        for bullet in to_remove:
            if bullet in bullets:
                bullets.remove(bullet)

        # ── HUD: ammo display ──
        draw_ammo(window_screen, ammo)

        # ── HUD: score (top right) ──
        score_txt = font.render(f"score: {score}", True, (255, 255, 255))
        window_screen.blit(score_txt, (WINDOW_WIDTH - score_txt.get_width() - 20, 20))

        # ── HUD: player HP (top left) ──
        hp_txt = font.render(f"hp: {player_hp}", True, (255, 80, 80))
        window_screen.blit(hp_txt, (20, 20))

        # ── HUD: difficulty label (top center) ──
        diff_color = settings['color']
        diff_txt   = small_font.render(f"difficulty: {settings['label'].upper()}", True, diff_color)
        window_screen.blit(diff_txt, (WINDOW_WIDTH // 2 - diff_txt.get_width() // 2, 20))

        # ── HUD: wave number ──
        wave_txt = small_font.render(f"wave: {wave_number}", True, (255, 220, 100))
        window_screen.blit(wave_txt, (WINDOW_WIDTH // 2 - wave_txt.get_width() // 2, 55))

        # ── HUD: enemy counter ──
        enemy_txt = small_font.render(f"enemies: {enemies_spawned}/{Max_Enemies}", True, (200, 180, 180))
        window_screen.blit(enemy_txt, (WINDOW_WIDTH // 2 - enemy_txt.get_width() // 2, 90))

        # ── Countdown to next wave ──
        if (not wave_in_progress and
            enemies_spawned < Max_Enemies and
            wave_number     < final_boss_wave):
            secs     = max(0, (wave_delay - wave_timer) // 60)   # Convert frames to seconds
            next_txt = pixel_font.render(f"next wave in {secs}...", True, (255, 180, 60))
            window_screen.blit(next_txt, (WINDOW_WIDTH // 2 - next_txt.get_width() // 2, WINDOW_HEIGHT // 2 - 40))

        # ── Wave announcement banner (fades out over wave_label_timer frames) ──
        if wave_label_timer > 0:
            alpha = min(255, wave_label_timer * 4)   # Fade from opaque to transparent

            if wave_number == final_boss_wave:
                color = (180, 30, 200)
                text  = f"WAVE {wave_number} - DEMON LORD!"
            elif wave_number == Boss_wave:
                color = (255, 80, 80)
                text  = f"WAVE {wave_number} - MINI BOSS!"
            else:
                color = (255, 220, 100)
                text  = f"WAVE {wave_number}"

            banner = big_font.render(text, True, color)
            banner.set_alpha(alpha)   # Apply fade transparency
            window_screen.blit(banner, (WINDOW_WIDTH // 2 - banner.get_width() // 2, WINDOW_HEIGHT // 2 - 60))

        # ── Reload bar (bottom left, shows reload progress) ──
        if reloading:
            reload_progress = 1 - (reload_timer / Reload_time)   # 0.0 at start, 1.0 when done
            bar_width       = int(240 * reload_progress)          # How wide to draw the bar
            pygame.draw.rect(window_screen, (60, 60, 60),    (20, WINDOW_HEIGHT - 80, 240, 14), border_radius=7)  # Empty bar
            pygame.draw.rect(window_screen, (255, 220, 0),   (20, WINDOW_HEIGHT - 80, bar_width, 14), border_radius=7)  # Filled bar
            txt = font.render("RELOADING...", True, (255, 220, 0))
            window_screen.blit(txt, (20, WINDOW_HEIGHT - 110))
        elif ammo == 0:
            # ── Show prompt if out of ammo but not auto-reloading ──
            txt = font.render("PRESS R TO RELOAD", True, (255, 80, 80))
            window_screen.blit(txt, (20, WINDOW_HEIGHT - 110))

        # ── Draw the crosshair on top of everything else ──
        aim_group.update()
        aim_group.draw(window_screen)

        pygame.display.update()   # Push everything we drew to the actual screen
        clock.tick(60)            # Limit to 60 FPS so the game runs the same speed on all machines

        if player_hp <= 0:
            return score, 'lose'

        if all_enemies_done:
            return score, 'win'

    return score, 'lose'


# =============================================================
#  GAME ENTRY POINT — Main loop that ties all screens together
# =============================================================
while True:
    result = main_menu()   # Show main menu, wait for player to click PLAY

    if result == 'play':
        chosen = difficulty_screen()   # Show difficulty screen

        if chosen is None:
            continue   # Player clicked BACK — go back to main menu

        # Add the difficulty label to the settings dict so run_game can display it
        settings = LEVELS[chosen]
        settings['label'] = chosen

        while True:
            score, outcome = run_game(settings)   # Play the game!

            if outcome == 'win':
                result = result_screen("YOU SURVIVED!", (80, 255, 120), score)
            else:
                result = result_screen("GAME OVER", (255, 60, 60), score)

            if result == 'menu':
                break   # Break the inner while → go back to main menu
            # If result == 'retry', the inner while loops and run_game is called again

pygame.quit()   # Clean up pygame when the outer loop exits
