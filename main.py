# Original Brawler Game Author: Coding with Russ
# Modifications: Calculator Integration and Turn-Based Game 

import pygame
from pygame import mixer
from fighter import Fighter
import turtle
import threading
import sys 
import random
import re

mixer.init()
pygame.init()

# Create game window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Differential Duel")

# Set framerate
clock = pygame.time.Clock()
FPS = 60

# Define colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Input box state
input_text = ""
input_box = pygame.Rect(90, 540, 860, 40)  # Moved right to make room for "y=" label
input_font = pygame.font.SysFont("consolas", 28)
label_font = pygame.font.SysFont("consolas", 32, bold=True)  # Font for "y=" label
input_color = (200, 200, 200)
input_active = True
input_locked = False
turn_ready = False
player_attack_complete = False
enemy_attack_complete = False

# Validation state
used_functions = set()  # Track used functions to prevent reuse
error_message = ""
error_display_time = 0
ERROR_DISPLAY_DURATION = 3000  # Show error for 3 seconds
current_turtle_window = None  # Track current turtle window for cleanup

# Define game variables
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]#player scores. [P1, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000

# Define fighter variables
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 56]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 107]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

# Load music and sounds
pygame.mixer.music.load("assets/audio/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_fx = pygame.mixer.Sound("assets/audio/sword.wav")
sword_fx.set_volume(0.5)
magic_fx = pygame.mixer.Sound("assets/audio/magic.wav")
magic_fx.set_volume(0.75)

# Load background image
bg_image = pygame.image.load("assets/images/background/background.jpg").convert_alpha()

# Load spritesheets
warrior_sheet = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
wizard_sheet = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()

# Load vicory image
victory_img = pygame.image.load("assets/images/icons/victory.png").convert_alpha()

# Define number of steps in each animation
WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

# Define font
count_font = pygame.font.Font("assets/fonts/turok.ttf", 80)
score_font = pygame.font.Font("assets/fonts/turok.ttf", 30)
error_font = pygame.font.Font("assets/fonts/turok.ttf", 20)

def validate_equation(equation):
    """
    Validates if the equation contains only allowed mathematical expressions
    Returns (is_valid, error_message)
    """
    if not equation.strip():
        return False, "Please enter an equation"
    
    # Normalize the equation - replace ^ with ** for Python
    normalized = equation.replace("^", "**").replace(" ", "")
    
    # Check if already used
    if normalized.lower() in used_functions:
        return False, "Function already used! Try a different equation"
    
    # Define allowed patterns
    allowed_chars = r'[x0-9+\-*/().^]'
    allowed_functions = ['sin', 'cos', 'tan', 'csc', 'sec', 'cot', 'log', 'ln', 'sqrt', 'abs', 'exp']
    
    # Must contain 'x' (the variable)
    if 'x' not in normalized.lower():
        return False, "Equation must contain variable 'x'"
    
    # Check for valid characters and functions
    temp_eq = normalized.lower()
    
    # Remove allowed functions from string for character checking
    for func in allowed_functions:
        temp_eq = temp_eq.replace(func, '')
    
    # Remove 'e' (Euler's number) if present
    temp_eq = temp_eq.replace('e', '')
    
    # Check if remaining characters are allowed
    if not re.match(r'^[x0-9+\-*/().^]*$', temp_eq):
        invalid_chars = set(temp_eq) - set('x0123456789+-*/().^')
        return False, f"Invalid characters: {', '.join(invalid_chars)}"
    
    # Basic syntax validation - check for balanced parentheses
    if equation.count('(') != equation.count(')'):
        return False, "Unbalanced parentheses"
    
    # Check for empty operators (like x + + x)
    if re.search(r'[+\-*/]{2,}', equation.replace('**', '*')):
        return False, "Invalid operator sequence"
    
    return True, ""

# Function for drawing text
def draw_text(text, font, text_col, x, y):
  img = font.render(text, True, text_col)
  screen.blit(img, (x, y))

def run_derivative_grapher(expr):
  from graphing_calculator import main as run_graph
  sys.argv = [sys.argv[0]]  # reset args
  input_thread = threading.Thread(target=run_graph, args=(expr,))
  input_thread.daemon = True
  input_thread.start()
  current_turtle_window = input_thread

# Function for drawing background
def draw_bg():
  scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
  screen.blit(scaled_bg, (0, 0))

# Function for drawing fighter health bars
def draw_health_bar(health, x, y):
  ratio = health / 100
  pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
  pygame.draw.rect(screen, RED, (x, y, 400, 30))
  pygame.draw.rect(screen, YELLOW, (x, y, 400 * ratio, 30))

def draw_input_box():
  # Draw "y=" label
  label_surface = label_font.render("y=", True, WHITE)
  screen.blit(label_surface, (input_box.x - 40, input_box.y + 5))
  
  # Change color based on validation state
  current_color = input_color
  if error_message and pygame.time.get_ticks() - error_display_time < ERROR_DISPLAY_DURATION:
    current_color = RED
  elif input_text.strip():
    is_valid, _ = validate_equation(input_text)
    current_color = GREEN if is_valid else RED
  
  pygame.draw.rect(screen, current_color, input_box, 3)  # Made border thicker
  text_surface = input_font.render(input_text, True, WHITE)
  screen.blit(text_surface, (input_box.x + 10, input_box.y + 8))
  
  # Display error message if there is one - made more visible
  if error_message and pygame.time.get_ticks() - error_display_time < ERROR_DISPLAY_DURATION:
    # Add background rectangle for better visibility
    error_surface = error_font.render(error_message, True, WHITE)
    error_rect = error_surface.get_rect()
    error_rect.x = input_box.x
    error_rect.y = input_box.y - 35
    
    # Draw semi-transparent background
    error_bg = pygame.Surface((error_rect.width + 20, error_rect.height + 10))
    error_bg.fill(RED)
    error_bg.set_alpha(200)  # Semi-transparent
    screen.blit(error_bg, (error_rect.x - 10, error_rect.y - 5))
    
    # Draw error text
    screen.blit(error_surface, (error_rect.x, error_rect.y))

def calculate_damage(equation):
    base_damage = len(equation)

    # Define weights for complex functions
    complexity_weights = {
        'sin': 1,
        'cos': 1,
        'tan': 1,
        'log': 2,
        'sqrt': 2,
        'ln': 2,
        'exp': 3
    }

    equation_lower = equation.lower()
    bonus_damage = 0

    # Add weighted bonus for each function found
    for func, weight in complexity_weights.items():
        if re.search(r'\b' + func + r'\b', equation_lower):
            bonus_damage += weight

    damage = base_damage + bonus_damage * 1.5
    return damage

# Instances of fighters
fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_fx)
fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, magic_fx)

# Game state variables
game_state = "waiting_input"  # "waiting_input", "player_attacking", "enemy_attacking"
attack_start_time = 0
ATTACK_DURATION = 800  # Duration for each attack phase

# GAME LOOP
run = True
while run:

  clock.tick(FPS)

  # Draw background
  draw_bg()

  # Show player stats
  draw_health_bar(fighter_1.health, 20, 20)
  draw_health_bar(fighter_2.health, 580, 20)
  draw_text("P1: " + str(score[0]), score_font, RED, 20, 60)
  draw_text("P2: " + str(score[1]), score_font, RED, 580, 60)

  # Update countdown
  if intro_count <= 0:
    current_time = pygame.time.get_ticks()
    
    if game_state == "waiting_input" and turn_ready:
      # Start player attack phase
      game_state = "player_attacking"
      attack_start_time = current_time
      
      # P1 attacks with animation and sound
      fighter_1.attack_type = 1
      fighter_1.attacking = True
      fighter_1.attack(fighter_2)
      
    elif game_state == "player_attacking":
      # Check if player attack is complete
      damage = calculate_damage(input_text)
      fighter_2.health -= damage
      print(f"\nDamage dealt:{damage}\nOpponent has {100-damage} health left!\n")
      game_state = "enemy_attacking"
      attack_start_time = current_time

      if current_time - attack_start_time >= ATTACK_DURATION:
        # P2 counterattacks with random chance to hit
        if random.random() < 0.9:  # 90% chance to hit
          fighter_2.attack_type = random.choice([1, 2])  # Random attack type
          fighter_2.attacking = True
          fighter_2.attack(fighter_1)
        else:
          # Miss - just do animation without damage
          fighter_2.attack_type = random.choice([1, 2])
          fighter_2.attacking = True
          # Don't call attack method, so no damage/sound
          
    elif game_state == "enemy_attacking":
    # Delay enemy attack (e.g. 500 ms after player's attack)
      if current_time - attack_start_time >= 500 and not fighter_2.attacking:
        if random.random() < 0.9:
          fighter_2.attack_type = random.choice([1, 2])
          fighter_2.attack_cooldown = 0  # ensure cooldown isn't blocking
          fighter_2.attack(fighter_1)
        else:
          fighter_2.attack_type = random.choice([1, 2])
          fighter_2.attacking = True  # play animation only

    # End enemy attack phase after full duration
      if current_time - attack_start_time >= ATTACK_DURATION:
        game_state = "waiting_input"
        turn_ready = False
        input_locked = False
        input_text = ""
        fighter_1.attacking = False
        fighter_2.attacking = False

  else:
    # Display count timer
    draw_text(str(intro_count), count_font, RED, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3)
    # Update count timer
    if (pygame.time.get_ticks() - last_count_update) >= 1000:
      intro_count -= 1
      last_count_update = pygame.time.get_ticks()

  # Update fighters
  fighter_1.update()
  fighter_2.update()

  # Draw fighters
  fighter_1.draw(screen)
  fighter_2.draw(screen)

  # Check for player defeat
  if round_over == False:
    if fighter_1.alive == False:
      score[1] += 1
      round_over = True
      round_over_time = pygame.time.get_ticks()
      print("Opponent's Victory")
    elif fighter_2.alive == False:
      score[0] += 1
      round_over = True
      round_over_time = pygame.time.get_ticks()
      print("You are a Winner")
  else:
    # Display victory image
    screen.blit(victory_img, (360, 150))
    if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
      round_over = False
      intro_count = 3
      game_state = "waiting_input"
      # Reset used functions for new round
      used_functions.clear()
      fighter_1 = Fighter(1, 200, 310, False, WARRIOR_DATA, warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_fx)
      fighter_2 = Fighter(2, 700, 310, True, WIZARD_DATA, wizard_sheet, WIZARD_ANIMATION_STEPS, magic_fx)

  # THE EVENT HANDLER
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      run = False
    elif event.type == pygame.KEYDOWN and input_active and not input_locked and game_state == "waiting_input":
        if event.key == pygame.K_RETURN:
            if input_text.strip() != "":
                is_valid, error_msg = validate_equation(input_text)
                if is_valid:
                    print("Valid equation entered:", input_text)
                    # Add to used functions (normalized)
                    normalized_input = input_text.replace("^", "**").replace(" ", "").lower()
                    used_functions.add(normalized_input)
                    
                    run_derivative_grapher(input_text)
                    turn_ready = True
                    input_locked = True
                    error_message = ""  # Clear any previous error
                else:
                    print("Invalid equation:", error_msg)
                    error_message = error_msg
                    error_display_time = pygame.time.get_ticks()

        elif event.key == pygame.K_BACKSPACE:
            input_text = input_text[:-1]
            # Clear error when user starts typing again
            if error_message:
                error_message = ""
        else:
            input_text += event.unicode
            # Clear error when user starts typing again
            if error_message:
                error_message = ""

  # Update display
  if game_state == "waiting_input":
    draw_input_box()
  pygame.display.update()

# EXIT PYGAME
pygame.quit()
