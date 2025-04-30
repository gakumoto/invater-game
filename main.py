import pygame
import sys
import os
import random

# --- パス設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(filename):
    return os.path.join(BASE_DIR, filename)

# --- 初期化 ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("インベーダー風ゲーム")
clock = pygame.time.Clock()

# --- 音読み込み ---
pygame.mixer.init()
pygame.mixer.music.load(resource_path("bgm.mp3"))
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

hit_sound = pygame.mixer.Sound(resource_path("papa.mp3"))
boss_music = pygame.mixer.Sound(resource_path("boss.mp3"))

# --- 画像読み込み ---
background_img = pygame.image.load(resource_path("background.jpg"))
player_img = pygame.image.load(resource_path("player.png"))
enemy_img = pygame.image.load(resource_path("enemy.png"))
bullet_img = pygame.image.load(resource_path("bullet.png"))
boss_img = pygame.image.load(resource_path("boss.png"))

# --- リサイズ ---
player_img = pygame.transform.scale(player_img, (50, 30))
enemy_img = pygame.transform.scale(enemy_img, (40, 30))
bullet_img = pygame.transform.scale(bullet_img, (5, 10))
boss_img = pygame.transform.scale(boss_img, (120, 60))

# --- プレイヤー設定 ---
player_x = WIDTH // 2
player_y = HEIGHT - 60
player_speed = 5

# --- 弾設定 ---
player_bullets = []
enemy_bullets = []
boss_bullets = []

# --- 敵設定（個別速度・向き） ---
enemy_rows, enemy_cols = 4, 8
enemies = []
for row in range(enemy_rows):
    for col in range(enemy_cols):
        x = 80 + col * 70
        y = 50 + row * 50
        speed = random.uniform(0.5, 1.2)
        direction = random.choice([-1, 1])
        enemies.append({'rect': pygame.Rect(x, y, 40, 30), 'speed': speed, 'dir': direction, 'shoot_timer': random.randint(60, 300)})

# --- スコアとフォント ---
score = 0
font = pygame.font.SysFont(None, 36)

# --- ボス設定 ---
boss_active = False
boss_health = 50
boss_rect = pygame.Rect(WIDTH // 2 - 60, 80, 120, 60)
boss_direction = 2
boss_shoot_timer = 0
boss_warning_displayed = False

# --- ゲームループ ---
running = True
while running:
    screen.blit(background_img, (0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # プレイヤー操作
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - 50:
        player_x += player_speed
    if keys[pygame.K_SPACE]:
        if len(player_bullets) < 5:
            player_bullets.append(pygame.Rect(player_x + 22, player_y, 5, 10))

    # 弾移動
    for b in player_bullets[:]:
        b.y -= 10
        if b.y < 0:
            player_bullets.remove(b)

    for b in enemy_bullets[:]:
        b.y += 6
        if b.y > HEIGHT:
            enemy_bullets.remove(b)

    for b in boss_bullets[:]:
        b.y += 6
        if b.y > HEIGHT:
            boss_bullets.remove(b)

    # 敵移動と反撃
    for enemy in enemies:
        e = enemy['rect']
        e.x += enemy['speed'] * enemy['dir']
        # ランダムにふらつかせる
        e.y += random.uniform(-0.3, 0.3)

        # 画面端で反転
        if e.x < 0 or e.x > WIDTH - 40:
            enemy['dir'] *= -1

        # ランダム反撃
        enemy['shoot_timer'] -= 1
        if enemy['shoot_timer'] <= 0:
            enemy_bullets.append(pygame.Rect(e.centerx, e.bottom, 5, 10))
            enemy['shoot_timer'] = random.randint(90, 300)

    # 敵に弾が当たる
    for b in player_bullets[:]:
        for enemy in enemies[:]:
            if b.colliderect(enemy['rect']):
                player_bullets.remove(b)
                enemies.remove(enemy)
                hit_sound.play()
                score += 10
                break

    # 敵全滅 → ボス出現
    if not enemies and not boss_active and not boss_warning_displayed:
        boss_warning_displayed = True
        pygame.mixer.music.stop()
        screen.fill((0, 0, 0))
        warning_text = font.render("WARNING!! BOSS APPROACHING", True, (255, 0, 0))
        screen.blit(warning_text, warning_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()
        pygame.time.wait(2000)
        boss_active = True
        boss_music.play(-1)

    # ボス回避AI（弾回避）
    if boss_active:
        for b in player_bullets:
            if boss_rect.y < b.y < boss_rect.y + 120 and abs(boss_rect.centerx - b.centerx) < 100:
                if b.centerx < boss_rect.centerx:
                    boss_rect.x += 5
                else:
                    boss_rect.x -= 5

        # ランダムに左右移動
        boss_rect.x += boss_direction + random.choice([-1, 0, 1])
        if boss_rect.left <= 0 or boss_rect.right >= WIDTH:
            boss_direction *= -1

        # ボス攻撃
        boss_shoot_timer += 1
        if boss_shoot_timer > 50:
            boss_bullets.append(pygame.Rect(boss_rect.centerx, boss_rect.bottom, 6, 12))
            boss_shoot_timer = 0

        # プレイヤー弾がボスに当たる
        for b in player_bullets[:]:
            if b.colliderect(boss_rect):
                player_bullets.remove(b)
                boss_health -= 1
                hit_sound.play()
                if boss_health <= 0:
                    boss_active = False
                    boss_music.stop()
                    score += 100
                    screen.fill((0, 0, 0))
                    win = font.render("YOU WIN!", True, (0, 255, 0))
                    screen.blit(win, win.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
                    pygame.display.flip()
                    pygame.time.wait(3000)
                    running = False

    # --- ゲームオーバー判定（敵弾 or ボス弾） ---
    player_rect = pygame.Rect(player_x, player_y, 50, 30)
    for b in enemy_bullets + boss_bullets:
        if b.colliderect(player_rect):
            boss_music.stop()
            screen.fill((0, 0, 0))
            game_over = font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(game_over, game_over.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            pygame.display.flip()
            pygame.time.wait(2000)
            running = False

    # --- 描画 ---
    screen.blit(player_img, (player_x, player_y))
    for enemy in enemies:
        screen.blit(enemy_img, enemy['rect'])
    for b in player_bullets:
        screen.blit(bullet_img, (b.x, b.y))
    for b in enemy_bullets + boss_bullets:
        pygame.draw.rect(screen, (255, 100, 100), b)
    if boss_active:
        screen.blit(boss_img, boss_rect)
        boss_hp = font.render(f"Boss HP: {boss_health}", True, (255, 200, 200))
        screen.blit(boss_hp, (WIDTH - 200, 10))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()