import pygame
import os
import time
import random
import mysql.connector
pygame.font.init()
pygame.init()

infoObject = pygame.display.Info()
WIDTH = infoObject.current_w
HEIGHT = infoObject.current_h
rData=""

WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Cosmic Conquest")

enemy1 = pygame.image.load(os.path.join("assets", "enemy1.png"))
enemy2 = pygame.image.load(os.path.join("assets", "enemy2.png"))
enemy3 = pygame.image.load(os.path.join("assets", "enemy3.png"))
playerShip = pygame.image.load(os.path.join("assets", "player.png"))
bullet1 = pygame.image.load(os.path.join("assets", "bullet.png"))
bullet2 = pygame.image.load(os.path.join("assets", "bullet.png"))
bullet3 = pygame.image.load(os.path.join("assets", "bullet.png"))
bullet4 = pygame.image.load(os.path.join("assets", "bullet.png"))

BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background.png")), (WIDTH, HEIGHT))

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="mysql",     
        database="game_scores" 
    )

def create_table(cursor):
    global rData
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        high_score INT DEFAULT 0
    )
    """)
    

def save_score(cursor, username, score):
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if user:
        if score > user[2]:
            cursor.execute("UPDATE users SET high_score = %s WHERE username = %s", (score, username))
    else:
        cursor.execute("INSERT INTO users (username, high_score) VALUES (%s, %s)", (username, score))

class Laser:
    def __init__(self, x, y, img):
        self.x = x + 15
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)

class Ship:
    COOLDOWN = 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = playerShip
        self.laser_img = bullet4
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width() * (self.health / self.max_health), 10))

class Enemy(Ship):
    COLOR_MAP = {
        "red": (enemy1, bullet1),
        "green": (enemy2, bullet2),
        "blue": (enemy3, bullet3)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x + 15, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def main(username):
    db = connect_db()
    cursor = db.cursor()
    create_table(cursor)
    
    run = True
    FPS = 60
    level = 0
    lives = 5
    main_font = pygame.font.SysFont("futura", 50)
    lost_font = pygame.font.SysFont("futura", 60)

    enemies = []
    wave_length = 5
    enemy_vel = 1

    player_vel = 8
    laser_vel = 8

    player = Player(300, 630)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BG, (0, 0))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        WIN.blit(level_label, (10, 10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255, 255, 255))
            WIN.blit(lost_label, (WIDTH / 2 - lost_label.get_width() / 2, 350))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1

        if lost:
            if lost_count > FPS * 3:
                save_score(cursor, username, level * 100)
                db.commit()
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player.x - player_vel > 0:  # left
            player.x -= player_vel
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_w] and player.y - player_vel > 0:  # up
            player.y -= player_vel
        if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT:  # down
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel, player)

            if random.randrange(0, 2 * 60) == 1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        player.move_lasers(-laser_vel, enemies)

def login_screen():

    title_font = pygame.font.SysFont("futura", 70)
    input_box = pygame.Rect(WIDTH / 2 - 100, HEIGHT / 2, 200, 50)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    font = pygame.font.SysFont('futura', 40)

    run = True
    while run:
        WIN.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        main(text)
                        run = False
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        txt_surface = font.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        WIN.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(WIN, color, input_box, 2)

        title_label = title_font.render("Enter your name", 1, (255, 255, 255))
        WIN.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, HEIGHT / 4))
        
        highscore_label = title_font.render("HighScores", 1, (255, 255, 255))
        WIN.blit(highscore_label, (WIDTH / 2 - highscore_label.get_width() / 2, HEIGHT-HEIGHT/2.5))
        
        db = connect_db()
        num=2.5
        order=[]
        high=0
        cursor = db.cursor()
        cursor.execute("Select * from users")
        a1=cursor.fetchall()
        rData = sorted(a1, key=lambda x:(-x[2], x[1]))

        for i in rData:
            k=i[1:]
            num+=50
            height1=HEIGHT-HEIGHT/2.8
            res = ' '.join([str(s) for s in k])
            retrievedData = title_font.render(res, 1, (255, 255, 255))
            WIN.blit(retrievedData, (WIDTH / 2 - retrievedData.get_width() / 2, height1+num))

        pygame.display.update()

    pygame.quit()

login_screen()
