# Original Brawler Game Author: Coding with Russ
# Modifications: Calculator Integration and Turn-Based Game 

import pygame
import random

class Fighter():
  def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, sound):
    self.player = player
    self.size = data[0]
    self.image_scale = data[1]
    self.offset = data[2]
    self.flip = flip
    self.animation_list = self.load_images(sprite_sheet, animation_steps)
    self.action = 0#0:idle #1:run (won't be used) #2:jump (won't be used) #3:attack1 #4: attack2 #5:hit #6:death
    self.frame_index = 0
    self.image = self.animation_list[self.action][self.frame_index]
    self.update_time = pygame.time.get_ticks()
    self.rect = pygame.Rect((x, y, 80, 180))
    self.vel_y = 0
    self.running = False
    self.jump = False
    self.attacking = False
    self.attack_type = 0
    self.attack_cooldown = 0
    self.attack_sound = sound
    self.hit = False
    self.health = 100
    self.alive = True


  def load_images(self, sprite_sheet, animation_steps):
    #extract images from spritesheet
    animation_list = []
    for y, animation in enumerate(animation_steps):
      temp_img_list = []
      for x in range(animation):
        temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
        temp_img_list.append(pygame.transform.scale(temp_img, (self.size * self.image_scale, self.size * self.image_scale)))
      animation_list.append(temp_img_list)
    return animation_list


  # Handles animation updates
  def update(self):
    # Checks what action the player is performing
    if self.health <= 0:
      self.health = 0
      self.alive = False
      self.update_action(6)#6:death
    elif self.hit == True:
      self.update_action(5)#5:hit
    elif self.attacking == True:
      if self.attack_type == 1:
        self.update_action(3)#3:attack1
      elif self.attack_type == 2:
        self.update_action(4)#4:attack2
    else:
      self.update_action(0)#0:idle

    animation_cooldown = 50
    # Update image
    self.image = self.animation_list[self.action][self.frame_index]
    # Check if enough time has passed since the last update
    if pygame.time.get_ticks() - self.update_time > animation_cooldown:
      self.frame_index += 1
      self.update_time = pygame.time.get_ticks()
    # Check if the animation has finished
    if self.frame_index >= len(self.animation_list[self.action]):
      # If the player is dead then end the animation
      if self.alive == False:
        self.frame_index = len(self.animation_list[self.action]) - 1
      else:
        self.frame_index = 0
        # Check if an attack was executed
        if self.action == 3 or self.action == 4:
          self.attacking = False
          self.attack_cooldown = 20
        # Check if damage was taken
        if self.action == 5:
          self.hit = False
          # If the player was in the middle of an attack, then the attack is stopped
          self.attacking = False
          self.attack_cooldown = 20


  def attack(self, target):
    # Always attack during turn-based phase
    self.attacking = True
    self.attack_sound.play()

    # OLD VERSION
    #damage = random.randint(5, 15)
    #target.health -= damage
    
    # Randomize damage ONLY for fighter_2 (opponent)
    if self.player == 2:
      damage = random.randint(5, 35)
      target.health -= damage
      print(f"\nDamage received:{damage}\nYou have {100-damage} health left!\n")

    # OLD VERSION
    #elif self.player == 1: 
      #damage = 10
      #target.health -= damage

    target.hit = True

    # Optional: set cooldown to prevent overlapping logic
    self.attack_cooldown = 20

    # Deal damage and trigger hit animation
  def update_action(self, new_action):
    # Check if the new action is different to the previous one
    if new_action != self.action:
      self.action = new_action
      # Update the animation settings
      self.frame_index = 0
      self.update_time = pygame.time.get_ticks()

  def draw(self, surface):
    img = pygame.transform.flip(self.image, self.flip, False)
    surface.blit(img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - (self.offset[1] * self.image_scale)))
