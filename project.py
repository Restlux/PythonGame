import pygame
import random
import math

# Initialize pygame
pygame.init()

# Get monitor's screen width and height
infoObject = pygame.display.Info()
screen_width = infoObject.current_w
screen_height = infoObject.current_h

# Create the screen in full-screen mode
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

# Load Background Image and scale it to full-screen size
backgroundImg = pygame.image.load('background.png')
backgroundImg = pygame.transform.scale(backgroundImg, (screen_width, screen_height))

# Title and Icon
pygame.display.set_caption("Space Invaders")

# Player
playerImg = pygame.image.load('player.png')
playerImg = pygame.transform.scale(playerImg, (64, 64))
playerX = screen_width // 2 - 32
playerY = screen_height - 100
playerX_vel = 0
playerY_vel = 0
acceleration = 0.2
friction = 0.98
player_lives = 3

# Enemy
enemyImg = []
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
enemy_bulletX = []
enemy_bulletY = []
enemy_bullet_active = []
enemy_bullet_speed = 5
num_of_enemies = 6
enemy_active = [True] * num_of_enemies  # Tracks whether an enemy is still active

for i in range(num_of_enemies):
    enemyImg.append(pygame.image.load('enemy.png'))
    enemyImg[i] = pygame.transform.scale(enemyImg[i], (64, 64))
    enemyX.append(random.randint(0, screen_width - 64))
    enemyY.append(random.randint(50, 150))
    enemyX_change.append(4)
    enemyY_change.append(40)
    enemy_bulletX.append(0)
    enemy_bulletY.append(screen_height + 100)  # Start bullets off-screen
    enemy_bullet_active.append(False)  # No active bullets at the start

# Bullet
bulletImg = pygame.image.load('bullet.png')
bulletImg = pygame.transform.scale(bulletImg, (32, 32))
bulletX = 0
bulletY = playerY
bulletY_change = 10
bullet_state = "ready"

# Score
score_value = 0
font = pygame.font.Font('freesansbold.ttf', 32)
textX = 10
textY = 10

# Game Over Text
over_font = pygame.font.Font('freesansbold.ttf', 64)


def show_score(x, y):
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (x, y))


def show_lives(x, y):
    lives_text = font.render("Lives : " + str(player_lives), True, (255, 255, 255))
    screen.blit(lives_text, (x, y + 40))


def game_over_text():
    over_text = over_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(over_text, (screen_width // 2 - 200, screen_height // 2 - 50))


def player(x, y):
    screen.blit(playerImg, (x, y))


def enemy(x, y, i):
    if enemy_active[i]:  # Only draw enemy if it's active
        screen.blit(enemyImg[i], (x, y))


def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x + 16, y + 10))


def is_collision(x1, y1, x2, y2, hitbox_radius):
    distance = math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))
    return distance < hitbox_radius


def fire_enemy_bullet(enemy_x, enemy_y, i):
    enemy_bulletX[i] = enemy_x + 16
    enemy_bulletY[i] = enemy_y + 64
    enemy_bullet_active[i] = True  # Mark bullet as active


# Game Loop
running = True
while running:

    # Draw the background image
    screen.blit(backgroundImg, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Player bullet control
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and bullet_state == "ready":
                bulletX = playerX  # Set bullet to player's current position
                fire_bullet(bulletX, bulletY)

    # Detect keystrokes for movement
    keys = pygame.key.get_pressed()

    # Acceleration based on key presses
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        playerX_vel -= acceleration
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        playerX_vel += acceleration
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        playerY_vel -= acceleration
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        playerY_vel += acceleration

    # Apply friction to slow the player down gradually
    playerX_vel *= friction
    playerY_vel *= friction

    # Update player position with velocity
    playerX += playerX_vel
    playerY += playerY_vel

    # Wrap horizontally
    if playerX < -64:
        playerX = screen_width
    elif playerX > screen_width:
        playerX = -64

    # Vertical barriers
    if playerY <= 0:
        playerY = 0
    elif playerY >= screen_height - 64:
        playerY = screen_height - 64

    # Enemy Movement and shooting projectiles
    for i in range(num_of_enemies):
        if not enemy_active[i]:  # Skip inactive enemies
            continue

        # Enemy Movement
        enemyX[i] += enemyX_change[i]
        if enemyX[i] <= 0:
            enemyX_change[i] = 4
            enemyY[i] += enemyY_change[i]
        elif enemyX[i] >= screen_width - 64:
            enemyX_change[i] = -4
            enemyY[i] += enemyY_change[i]

        # Enemy shooting projectiles
        if not enemy_bullet_active[i] and random.randint(0, 100) < 5:  # Randomly fire bullets
            fire_enemy_bullet(enemyX[i], enemyY[i], i)

        # Move enemy bullet
        if enemy_bullet_active[i]:
            if enemy_bulletY[i] >= screen_height:  # Deactivate bullet if it goes off-screen
                enemy_bullet_active[i] = False
            else:
                enemy_bulletY[i] += enemy_bullet_speed  # Move bullet downward

            # Draw enemy bullet
            screen.blit(bulletImg, (enemy_bulletX[i], enemy_bulletY[i]))

            # Check for collision between enemy bullet and player
            if is_collision(enemy_bulletX[i], enemy_bulletY[i], playerX, playerY, 32):
                player_lives -= 1
                enemy_bullet_active[i] = False  # Deactivate bullet on hit

        # Check for game over
        if player_lives <= 0:
            running = False  # End the game

        enemy(enemyX[i], enemyY[i], i)

    # Player bullet movement
    if bulletY <= 0:
        bulletY = playerY
        bullet_state = "ready"

    if bullet_state == "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change

    # Check for bullet collision with enemies
    for i in range(num_of_enemies):
        if not enemy_active[i]:  # Skip inactive enemies
            continue

        collision = is_collision(bulletX, bulletY, enemyX[i], enemyY[i], 50)  # Larger hitbox radius
        if collision:
            bulletY = playerY
            bullet_state = "ready"
            score_value += 1
            enemy_active[i] = False  # Disable the enemy after it's shot

    # Draw the player
    player(playerX, playerY)

    # Show the score and lives
    show_score(textX, textY)
    show_lives(textX, textY)

    # Update the screen
    pygame.display.update()

# Close the game if lives are 0
pygame.quit()
