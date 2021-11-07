from random import randint
from classes import *

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

db_url = 'https://ham2021-bothe-default-rtdb.asia-southeast1.firebasedatabase.app/'
cred = credentials.Certificate("./key.json")
default_app = firebase_admin.initialize_app(cred, {'databaseURL':db_url})


player = None#Player(100,GROUND+PLAYER_SIZE,GROUND)
obstacles = []
pressed_keys = []
jumped = 0
objectTimer = 0
timer = 0
scene = START_SCENE
score = 0
pattern = Pattern()
items = []
mouse = [0,0,0]
character = 0
damagedTime = -255
highScore = False
savedScore = 0

def makeObstacle(cycle):
    global obstacles
    global objectTimer

    if objectTimer >= cycle:
        choice = random.randint(0,len(pattern.pattern)-1)
        objectTimer -= cycle
        for obs in pattern.interpret(choice):
            obstacles.append(obs)

def bulletMoveAndDraw(screen):
    global bullets

    bullets_copy = bullets.copy()
    popped = 0
    for i in range(len(bullets_copy)) :
        bullet = bullets_copy[i]
        bullet.move()
        bullet.draw(screen)
        if bullet.x + bullet.size/2 > SCREEN_WIDTH:
            bullets.pop(i-popped)
            popped += 1

def obstaclesMoveAndDraw(screen):
    global obstacles

    obstacles_copy = obstacles.copy()
    popped = 0
    for i in range(len(obstacles_copy)):
        obstacle = obstacles_copy[i]
        obstacle.move()
        obstacle.draw(screen)
        if obstacle.x + obstacle.xSize/2 <= 0:
            obstacles.pop(i - popped)
            popped += 1

def playerMoveAndDraw(screen,player):
    global scene
    global damagedTime
    global highScore
    global savedScore

    player.move()
    player.draw(screen)
    if player.collision(obstacles):
        if player.immune == 0 :
            damagedTime = timer
            player.hp -= 10
            player.immune = 100
        if player.hp <= 0:
            ref = db.reference()
            savedScore = score
            if ref.get() is None:
                ref.update({"best":score})
                highScore = True
            elif ref.get().get("best") < score:
                ref.update({"best":score})
                highScore = True
            scene = DIED_SCENE

def bulletHitObstacle():
    global bullets
    global obstacles
    global items

    bullets_copy = bullets.copy()
    popped = 0
    bullet_popped = 0
    for i in range(len(bullets_copy)):
        bullet = bullets_copy[i]
        if bullet.collision(obstacles) is not None:
            obstacle_idx = bullet.collision(obstacles)
            bulletInReal = obstacles[obstacle_idx-popped]

            bullet_hp = bullet.hp
            bullet.hp -= bulletInReal.hp
            bulletInReal.hp -= bullet_hp
            
            if bullet.hp <= 0 :
                bullets.pop(i-bullet_popped)
                bullet_popped += 1

            if bulletInReal.hp <= 0 :
                if not bulletInReal.item is None:
                    if bulletInReal.item % 1 == 0 and bulletInReal.item != 0:
                        items.append(Item(bulletInReal.x,bulletInReal.y,35,bulletInReal,bulletInReal.item))
                    elif bulletInReal.item != 0:
                        if random.random() < (bulletInReal.item % 1):
                            items.append(Item(bulletInReal.x,bulletInReal.y,35,bulletInReal,bulletInReal.item))
                obstacles.pop(obstacle_idx-popped)
                popped += 1

def itemMoveAndEat(screen,player):
    global items

    item_copy = items.copy()
    popped = 0
    for i in range(len(item_copy)):
        item = item_copy[i]
        item.move()
        item.draw(screen)
        if item.collision(player):
            item.eat(player)
            items.pop(i - popped)
            popped += 1
        if item.x + item.size <=0:
            items.pop(i-popped)
            popped += 1

def HPBarDraw(screen,obstacles):
    playerHP.draw(screen)
    for obstacle in obstacles:
        if obstacle.hp != obstacle.maxHP : ObstacleHPBar(obstacle).draw(screen)

def write(screen,text,pos,font,size,color,center = None):
    myfont = pygame.font.SysFont(font, size)

    textsurface = myfont.render(text, False, color)
    if center is None:
        text_rect = textsurface.get_rect(center=(pos[0], pos[1]))
        screen.blit(textsurface,text_rect)
    elif center:
        screen.blit(textsurface,pos)
    else:
        text_rect = textsurface.get_rect()
        text_rect.right = pos[0]
        screen.blit(textsurface,text_rect)

def getDamagedScreen(screen,damagedTime):
    redRect = pygame.Surface((SCREEN_WIDTH - 40,SCREEN_HEIGHT - 80),pygame.SRCALPHA)
    value = timer - damagedTime
    redRect.set_alpha(255 - value * 255 / 100)
    pygame.draw.rect(redRect,RED,pygame.Rect(0,0,SCREEN_WIDTH - 40,SCREEN_HEIGHT - 80),20)
    screen.blit(redRect, (20,40))

def startButton(screen):
    global scene

    centerPos = (SCREEN_WIDTH/2,SCREEN_HEIGHT*3/4)
    pygame.draw.circle(screen,WHITE,centerPos,50)
    startPos = (SCREEN_WIDTH/2+35,SCREEN_HEIGHT*3/4)
    secondPos = move(startPos,210,60)
    thirdPos = move(startPos,-210,60)
    pygame.draw.polygon(screen,BLACK,[startPos,secondPos,thirdPos])
    if isPointInCircle(mouse[0],mouse[1],centerPos[0],centerPos[1],50) and CLICK:
        scene = CHARACTER_CHOOSE_SCENE

def keyboard():
    global mouse
    global pressed_keys
    global jumped

    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[pygame.K_z]:
        player.attackCharging(screen)
    elif player is not None:
        player.attackUp()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.KEYDOWN and scene == GAME_SCENE :
            if event.key == pygame.K_z:
                player.attackDown()
            if event.key == pygame.K_SPACE:
                if jumped == 1:
                    player.Yforce += 10
                    jumped = -1
                if player.y == GROUND + player.size :
                    jumped = 1
                    player.Yforce = 10
        mouse = list(pygame.mouse.get_pos()) + [False]
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse[2] = True

def drawBG(screen,timer):
    global BGRects
    #BGRects = [BGRect((20,SCREEN_HEIGHT-20),100,2,5)]
    if timer%150*5/int(SPEED) == 0:
        y = random.randint(0,SCREEN_HEIGHT)
        size = random.randint(50,150)
        distance = random.randint(250,500)
        angleSpeed = random.randint(500,3000)
        BGRects.append(BGRect((SCREEN_WIDTH+size,y*math.sqrt(2)),size,distance,angleSpeed/10000))
    popped = 0
    for i in range(len(BGRects)):
        BGRects[i-popped].move(SPEED*5)
        BGRects[i-popped].draw(screen)
        if BGRects[i-popped].x + BGRects[i-popped].size * math.sqrt(2) <= 0:
            BGRects.pop(i-popped)
            popped += 1

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("DIE-NO GAME")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.mixer.init()
    pygame.mixer.music.load('Hope.mp3')
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.5)

    clock = pygame.time.Clock()
    while True:
        clock.tick(100)
        keyboard()
        
        CLICK = mouse[2]
        screen.fill(BLACK)
        if scene == START_SCENE :
            write(screen,'DIE-NO GAME',(SCREEN_WIDTH/2,SCREEN_HEIGHT/4),'./Binggrae-Bold.ttf',100,WHITE)
            startButton(screen=screen)
        elif scene == CHARACTER_CHOOSE_SCENE :
            startPos = (20,SCREEN_HEIGHT/3 + 10)
            pygame.draw.line(screen,WHITE,(0,startPos[1]-30),(SCREEN_WIDTH,startPos[1]-30),5)
            write(screen,'CHOOSE YOUR CHARACTER',(SCREEN_WIDTH/2,SCREEN_HEIGHT*5/6),'Comic Sans MS',50,WHITE)
            for i in range(len(PLAYER_LIST)):
                button = pygame.Rect(startPos[0] + SCREEN_WIDTH/12 * i + 10*i,startPos[1] ,SCREEN_WIDTH/12 - 20 ,SCREEN_HEIGHT/6 - 20)
                pygame.draw.rect(screen,WHITE,button)
                blackBlank = pygame.Rect(startPos[0] + SCREEN_WIDTH/12 * i + 10*i + 5,startPos[1] + 5 ,SCREEN_WIDTH/12 - 20 -10 ,SCREEN_HEIGHT/6 - 20 -10)
                pygame.draw.rect(screen,BLACK,blackBlank)
                PLAYER_LIST[i](button.x + button.width/2, -button.y-button.height/2,GROUND,(SCREEN_WIDTH/12 - 20 -10)*2/5).draw(screen)
                if isPointInRect(mouse[0],mouse[1],button):
                    PLAYER_LIST[i](SCREEN_WIDTH/4, -SCREEN_HEIGHT/6,GROUND,30).draw(screen)
                    write(screen,PLAYER_NAME_LIST[i],(SCREEN_WIDTH*3/4,SCREEN_HEIGHT/6),'Comic Sans MS',50,WHITE)
                    if CLICK:
                        player = PLAYER_LIST[i](100,GROUND+PLAYER_SIZE,GROUND,PLAYER_SIZE)
                        character = i
                        scene = GAME_SCENE
                        playerHP = PlayerHPBar(player)

        elif scene == GAME_SCENE :
            makeObstacle(100)
            drawBG(screen,timer)
            pygame.draw.line(screen,WHITE,(0,-GROUND),(SCREEN_WIDTH,-GROUND),5)
            bulletMoveAndDraw(screen)
            obstaclesMoveAndDraw(screen)
            playerMoveAndDraw(screen,player)
            if pressed_keys[pygame.K_z] and character == 1 and player.power != 0: Bullet(player,2,player.power).draw(screen)

            bulletHitObstacle()
            itemMoveAndEat(screen,player)
            HPBarDraw(screen,obstacles)
            if 1 in player.effect.keys():
                screen.blit(ENERGY_EFFECT_IMG,(230,10))
                if character == 0:
                    write(screen,str(player.effect[1]),(250,50),'Sans',20,WHITE)
                elif character == 1:
                    write(screen,str(round(player.effect[1]*20)),(250,50),'Sans',20,WHITE)
                elif character == 2:
                    write(screen,str(player.effect[1]),(250,50),'Sans',20,WHITE)
            getDamagedScreen(screen,damagedTime)
            player.immune = max(0,player.immune - 1)
            if player.immune != 0 :
                player.x = 100 + ((timer - damagedTime)**2 - 100 * (timer - damagedTime))/200

            objectTimer += 1
            timer += 1
            SPEED += 0.075
            write(screen,str(round(score)).rjust(10,'0'),(SCREEN_WIDTH-10,20),'Comic Sans MS',20,WHITE,0)
            score += SPEED
            
        elif scene == DIED_SCENE:
            write(screen,'YOU DIED',(SCREEN_WIDTH/2,SCREEN_HEIGHT/3),'Comic Sans MS',100,RED)
            write(screen,'SCORE : '+str(round(savedScore,3)),(SCREEN_WIDTH/2,SCREEN_HEIGHT/2),'Comic Sans MS',30,WHITE)
            if highScore : write(screen,'HIGH SCORE!',(SCREEN_WIDTH/2,SCREEN_HEIGHT/2+50),'Comic Sans MS',30,YELLOW)
            score = 0
            SPEED = 5
            objectTimer = 0
            timer = 0
            damagedTime = -255
            bullets.clear()
            obstacles = []
            items = []
            jumped = 0
            startButton(screen=screen)
        pygame.display.update()