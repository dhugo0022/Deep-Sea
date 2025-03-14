import os
import pygame
import sys

# Padronização dos ids do botões do mouse
MOUSE_LEFT_BUTTON = 1
MOUSE_RIGHT_BUTTON = 3

GENERAL_ASSETS_PATH = ["src", "assets"]

DEFAULT_FONT = "v5easter.ttf"
LOADED_FONTS = {}
LOADED_SOUNDS = {}

# Tirada de https://www.pygame.org/docs/tut/tom_games3.html#makegames-3
def load_image(*paths: str) -> pygame.Surface:
  """ 
    Carrega uma imagem a partir de um arquivo\n
    e retorna o objeto dela como uma superfície.
  """
  fullname = os.path.join(*GENERAL_ASSETS_PATH, "images", *paths)

  try:
    image = pygame.image.load(fullname).convert_alpha()
  except FileNotFoundError:
    print(f"Não foi possível carregar a imagem: {fullname}.")
    raise SystemExit
  
  return image

def load_sound(*paths: str) -> pygame.mixer.Sound:
  """ 
    Carrega um som a partir de um arquivo e\n
    retorna o objeto dele.
  """

  fullname = os.path.join(*GENERAL_ASSETS_PATH, "sounds", *paths)

  try:

    if fullname in LOADED_SOUNDS:
      return LOADED_SOUNDS[fullname]
    
    sound = pygame.mixer.Sound(fullname)
    LOADED_SOUNDS[fullname] = sound
  except FileNotFoundError:
    print(f"Não foi possível carregar o som: {fullname}.")
    raise SystemExit
  
  return sound

def load_music(*paths: str):
  """ 
    Carrega um som a partir de um arquivo e\n
    retorna o objeto dele.
  """

  fullname = os.path.join(*GENERAL_ASSETS_PATH, "sounds", *paths)

  try:
    pygame.mixer.music.load(fullname)
  except FileNotFoundError:
    print(f"Não foi possível carregar a musica: {fullname}.")
    raise SystemExit
  

def __load_font(path: str, size: int) -> pygame.font.Font:
  """ 
    Carrega uma fonte a partir de um arquivo e\n
    retorna o objeto dela.
  """
  
  if not pygame.font or not pygame.font.get_init():
    print(f"o módulo \"font\" do pygame foi importado incorretamente.")
    raise SystemExit


  fullname = os.path.join(*GENERAL_ASSETS_PATH, "fonts", path)

  try:
    font = pygame.font.Font(fullname, size)
  except FileNotFoundError:
    print(f"Não foi possível carregar a fonte: {fullname}.")
    raise SystemExit
  
  return font

def get_font(size: int) -> pygame.font.Font:
  '''
    Carrega uma fonte para um determinado tamanho. Caso\n
    a fonte já tenha sido carregada anteriormente ela\n
    será retornada.Caso contrário, a fonte será carregada\n
    e adicionada à lista de fontes carregadas.
  '''
  if size not in LOADED_FONTS:
    LOADED_FONTS[size] = __load_font(DEFAULT_FONT, size)

  return LOADED_FONTS[size]

def clip_image(image: pygame.surface.Surface, position: tuple[int, int], size: tuple[int, int]) -> pygame.Surface:
  """ 
    Corta a superfície de acordo com as posições e tamanhos fornecidos.\n
    Retorna a superfície cortada.
  """

  cache_image = image.copy()
  clip_rect = pygame.rect.Rect(position, size)
  cache_image.set_clip(clip_rect)
  clipped_image = cache_image.subsurface(cache_image.get_clip())
  return clipped_image.copy() 


def clip_sprites(image: pygame.Surface, sprite_size: tuple[int, int], scale_by_size: tuple[int, int] = None) -> list[pygame.Surface]:
  width, _ = image.get_size()
  sprite_clip_width, _ = sprite_size
  sprite_count = int(width / sprite_clip_width)

  sprites = []
  
  for index in range(1, sprite_count + 1):
    clip_x = (index - 1) * sprite_clip_width
    sprite = clip_image(image, (clip_x, 0), sprite_size)

    if scale_by_size:
      sprite = pygame.transform.scale_by(sprite, scale_by_size)

    sprites.append(sprite)
  
  return sprites

def sum_tuples(source: tuple[int], addition: tuple[int]) -> tuple:
  if len(source) != len(addition):
    sys.exit("As tuplas somadas devem ser do mesmo tamanho.")
    return
  
  # return tuple(map(lambda source_value,addition_value: source_value + addition_value, source, addition))
  return tuple([source_value + addition[source_index] for source_index, source_value in enumerate(source)])

def multiply_tuple_by_scalar(source: tuple[int], scalar: int) -> tuple:
  return tuple([value * scalar for value in source])

# Referência: https://www.pygame.org/wiki/FrameRateIndependentAnimation
LOOP = 0
ONCE = 1

class Anim:
    def __init__(self, frames: list[tuple[any, int]], mode: bool = LOOP):
        self.frames = frames
        self.playmode = mode

# TODO: entender como funciona cada parte do código e criar anotações para as partes do mesmo
class AnimCursor:
    def __init__(self):
        self.anim: Anim = None
        self.frame_num = 0
        self.current: any = None
        self.next: any = None
        self.played = []
        self.transition = 0.0
        self.playing = True
        self.playtime = 0.0
    
        self.frame_time = 0.0
        self.timeleft = 0.0
        self.playspeed = 1.0
        
    def use_anim(self, anim):
        self.anim = anim
        self.reset()
        
    def reset(self):
        self.current = self.anim.frames[0][0]
        self.timeleft = self.anim.frames[0][1]
        self.frame_time = self.timeleft
        self.next_frame = (self.frame_num + 1) % len(self.anim.frames)
        self.next = self.anim.frames[self.next_frame][0]
        self.frame_num = 0
        self.playtime = 0.0
        self.transition = 0.0
        
    def play(self, playspeed=1.0):
        self.playspeed = playspeed
        self.reset()
        self.unpause()
        
    def pause(self):
        self.playing = False
        
    def unpause(self):
        self.playing = True
        
    def update(self, td):
        td = td * self.playspeed
        self.played = []
        if self.playing:
            self.playtime += td
            self.timeleft -= td
            self.transition = self.timeleft / self.frame_time
                
            while self.timeleft <= 0.0:
                self.frame_num = (self.frame_num + 1) % len(self.anim.frames)
                if self.anim.playmode == ONCE and self.frame_num == 0:
                    self.pause()
                    return
                    
                next_frame = (self.frame_num + 1) % len(self.anim.frames)
                
                frame, time = self.anim.frames[self.frame_num]
                self.frame_time = time
                self.timeleft += time
                self.current = frame
                self.next = self.anim.frames[next_frame][0]
                self.played.append(frame)
                self.transition = self.timeleft / time
                
                if self.frame_num == 0:
                    self.playtime = self.timeleft