import os
import pygame
import numpy as np
import cv2

from PIL import Image

# ==========================================
# MA DURGA — SMOOTH PARTICLE FORMATION
# Original image colours | 60-second video
# ==========================================

IMAGE_PATH = "durga.png"
OUTPUT_PATH = "durga_smooth_particles.mp4"

WIDTH = 720
HEIGHT = 1280
FPS = 30

TOTAL_SECONDS = 60
FORMATION_SECONDS = 50
HOLD_SECONDS = 10

# Lower value = more particles and more detail.
# Start with 3 for a balance of detail and speed.
PARTICLE_STEP = 3

BACKGROUND = (2, 3, 10)

# ==========================================
# INITIALIZE PYGAME
# ==========================================

pygame.init()

screen = pygame.display.set_mode((540, 960))
pygame.display.set_caption(
    "Maa Durga - Smooth Particle Formation"
)

clock = pygame.time.Clock()

# ==========================================
# LOAD IMAGE
# ==========================================

if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(
        "durga.png ko main.py ke same folder mein rakho."
    )

image = Image.open(IMAGE_PATH).convert("RGB")

image.thumbnail(
    (WIDTH, HEIGHT),
    Image.Resampling.LANCZOS
)

# Create vertical canvas without stretching image
canvas = Image.new(
    "RGB",
    (WIDTH, HEIGHT),
    BACKGROUND
)

offset_x = (WIDTH - image.width) // 2
offset_y = (HEIGHT - image.height) // 2

canvas.paste(image, (offset_x, offset_y))

original = np.asarray(
    canvas,
    dtype=np.uint8
).copy()

# ==========================================
# EXTRACT IMAGE PIXELS
# ==========================================

brightness = original.max(axis=2)

# Select the visible parts of the image.
# This avoids filling the dark background with particles.
ys, xs = np.where(
    (brightness > 25)
    & (
        np.indices((HEIGHT, WIDTH))[0] % PARTICLE_STEP == 0
    )
    & (
        np.indices((HEIGHT, WIDTH))[1] % PARTICLE_STEP == 0
    )
)

target_x = xs.astype(np.float32)
target_y = ys.astype(np.float32)

# IMPORTANT:
# Every particle gets its actual colour from the image.
particle_colors = original[ys, xs].copy()

count = len(target_x)

print("Particles:", count)

# ==========================================
# RANDOM STARTING POSITIONS
# ==========================================

rng = np.random.default_rng(42)

start_x = rng.uniform(
    -WIDTH * 0.5,
    WIDTH * 1.5,
    count
).astype(np.float32)

start_y = rng.uniform(
    -HEIGHT * 0.5,
    HEIGHT * 1.5,
    count
).astype(np.float32)

# Each particle begins its journey at a slightly
# different time for a gradual, natural formation.
delay = rng.uniform(
    0.0,
    0.30,
    count
).astype(np.float32)

# Tiny individual movement offsets
phase = rng.uniform(
    0,
    np.pi * 2,
    count
).astype(np.float32)

# ==========================================
# VIDEO WRITER
# ==========================================

os.makedirs("output", exist_ok=True)

video_path = os.path.join(
    "output",
    OUTPUT_PATH
)

writer = cv2.VideoWriter(
    video_path,
    cv2.VideoWriter_fourcc(*"mp4v"),
    FPS,
    (WIDTH, HEIGHT)
)

if not writer.isOpened():
    pygame.quit()

    raise RuntimeError(
        "Video writer start nahi hua. OpenCV check karo."
    )

total_frames = TOTAL_SECONDS * FPS

# ==========================================
# SPARKLE PARTICLES
# ==========================================

sparkle_count = 120

sparkle_x = rng.uniform(
    0, WIDTH, sparkle_count
).astype(np.float32)

sparkle_y = rng.uniform(
    0, HEIGHT, sparkle_count
).astype(np.float32)

sparkle_speed = rng.uniform(
    8, 28, sparkle_count
).astype(np.float32)

# ==========================================
# ANIMATION LOOP
# ==========================================

frame_number = 0
running = True

try:

    while running and frame_number < total_frames:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                running = False

        time_now = frame_number / FPS

        # ==================================
        # FORMATION PROGRESS
        # ==================================

        progress = min(
            1.0,
            time_now / FORMATION_SECONDS
        )

        # Smooth ease-in-out curve
        eased = (
            6 * progress**5
            - 15 * progress**4
            + 10 * progress**3
        )

        # ==================================
        # CREATE DARK CANVAS
        # ==================================

        frame = np.empty(
            (HEIGHT, WIDTH, 3),
            dtype=np.uint8
        )

        frame[:] = BACKGROUND

        if progress < 1.0:

            # Individual particles gradually settle
            local_progress = np.clip(
                (progress - delay)
                / (1.0 - delay),
                0,
                1
            )

            # Smooth interpolation for each particle
            smooth = (
                local_progress**2
                * (3 - 2 * local_progress)
            )

            px = start_x + (
                target_x - start_x
            ) * smooth

            py = start_y + (
                target_y - start_y
            ) * smooth

            # Gentle movement that disappears as particles settle
            remaining = 1.0 - smooth

            px += (
                np.sin(time_now * 1.5 + phase)
                * 8.0
                * remaining
            )

            py += (
                np.cos(time_now * 1.3 + phase)
                * 8.0
                * remaining
            )

            px = np.clip(
                px.astype(np.int32),
                0,
                WIDTH - 1
            )

            py = np.clip(
                py.astype(np.int32),
                0,
                HEIGHT - 1
            )

            # Preserve exact source-image colours.
            # Brighten particles while preserving their original colours
            bright_colors = particle_colors.astype(np.float32) * 1.45 + 25

            bright_colors = np.clip(
            bright_colors, 0, 255
            ).astype(np.uint8)

            frame[py, px] = bright_colors

            # ==================================
            # COLOUR-MATCHED PARTICLE GLOW
            # ==================================

            # A limited subset receives a soft glow.
            # Glow colour comes from each particle's
            # own image colour, not a fixed gold colour.

            glow_indices = np.arange(
                0,
                count,
                12
            )

            gx = px[glow_indices]
            gy = py[glow_indices]

            gc = particle_colors[glow_indices]

            # Add subtle colour-matched light around
            # moving particles. Keep it restrained
            # to preserve the original image colours.
            for dx, dy, strength in (
                (-2, 0, 0.35),
                (2, 0, 0.35),
                (0, -2, 0.35),
                (0, 2, 0.35),
                (-1, 0, 0.55),
                (1, 0, 0.55),
                (0, -1, 0.55),
                (0, 1, 0.55),
                ):

                nx = np.clip(
                    gx + dx,
                    0,
                    WIDTH - 1
                )

                ny = np.clip(
                    gy + dy,
                    0,
                    HEIGHT - 1
                )

                existing = frame[ny, nx].astype(
                    np.float32
                )

                light = gc.astype(
                    np.float32
                ) * strength

                frame[ny, nx] = np.clip(
                    existing + light,
                    0,
                    255
                ).astype(np.uint8)

            # ==================================
            # SMOOTH FINAL REVEAL
            # ==================================

            # During the last 4 seconds of formation,
            # blend the particle image into the original.
            # This prevents the image from suddenly popping in.

            blend_start = FORMATION_SECONDS - 4

            if time_now > blend_start:

                alpha = np.clip(
                    (time_now - blend_start) / 4.0,
                    0,
                    1
                )

                # Smooth blend
                alpha = (
                    alpha * alpha * (3 - 2 * alpha)
                )

                frame = cv2.addWeighted(
                    frame,
                    1.0 - alpha,
                    original,
                    alpha,
                    0
                )

        else:

            # Final image uses the exact original
            # image colours and sharp details.
            frame = original.copy()

        # ==================================
        # FLOATING SPARKLES
        # ==================================

        # Subtle coloured sparkles around the image.
        # No large gold wash over the original artwork.

        for i in range(sparkle_count):

            sparkle_y[i] -= sparkle_speed[i] / FPS

            if sparkle_y[i] < 0:

                sparkle_y[i] = HEIGHT

                sparkle_x[i] = rng.uniform(
                    0, WIDTH
                )

            sx = int(sparkle_x[i])
            sy = int(sparkle_y[i])

            # Bright white-golden sparkle
            cv2.circle(
            frame,
            (sx, sy),
            3,
            (255, 245, 220),
            -1,
            cv2.LINE_AA
            )

        # Small bright centre
        cv2.circle(
        frame,
        (sx, sy),
        1,
        (255, 255, 255),
        -1,
        cv2.LINE_AA
        )

        # ==================================
        # WRITE VIDEO FRAME
        # ==================================

        writer.write(
            cv2.cvtColor(
                frame,
                cv2.COLOR_RGB2BGR
            )
        )

        # ==================================
        # LIVE PREVIEW
        # ==================================

        preview = cv2.resize(
            frame,
            (540, 960),
            interpolation=cv2.INTER_AREA
        )

        surface = pygame.surfarray.make_surface(
            np.transpose(preview, (1, 0, 2))
        )

        screen.blit(surface, (0, 0))

        pygame.display.flip()

        frame_number += 1

        clock.tick(FPS)

        if frame_number % (FPS * 5) == 0:

            print(
                f"Rendered {frame_number // FPS}"
                f"/{TOTAL_SECONDS} seconds"
            )

finally:

    writer.release()
    pygame.quit()

print("\nVideo completed!")
print("Saved to:", video_path)