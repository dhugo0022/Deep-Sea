from scene import Scene
from scenes.play import PlayScene
from libs.components import SpriteSource, Text, SpriteButton, Counter, Dropdown
from libs.game_components import SoundtrackToggle
from libs.utils import load_image
import pygame

class ConfigurationScene(Scene):

  def __init__(self):
    super().__init__("configuration", soundtrack_filename=["soundtracks", "8_bit_bossa_nova.ogg"])

  def setup(self):
    self.shared_state = {
      "initial_oxygen_tanks": 160,
      "map_size": 15,
      "player_count": 2,
      "difficulty": 0
    }

    self.background = load_image("background.png")
    self.background = pygame.transform.scale(self.background, pygame.display.get_window_size())

    window_width, window_height = pygame.display.get_window_size()
    center_x = window_width / 2

    game_title = Text(
      (center_x, 200),
      "Deep Sea",
      64,
      "white",
    )

    initial_option_y = game_title.get_y_position() + 70
    space_between_options = 10

    # Quantidade inicial de oxygênio

    initial_oxygen_tanks_handle = Text(
      (center_x - 60, initial_option_y),
      "Qtd. de oxygênio:",
      24,
      "white",
      text_offset=(0, -2),
      background_file_name=["small_banner.png"],
      background_scale_by_size=(1.6, 1.5)
    )

    initial_oxygen_tanks_counter = Counter(
      (center_x + 105, initial_option_y),

      160, 500, 5, self.shared_state["initial_oxygen_tanks"],

      24,
      "black",
      (0, -2),

      ["horizontal_strip.png"],
      ["buttons", "decrease.png"],
      ["buttons", "increase.png"],

      (40, 0),

      scale_by_size=(3, 3),
      button_sprite_size=(10, 10),
      button_disable_sprite_index=2,
      on_click=lambda new_size: self.shared_state.update({"initial_oxygen_tanks": new_size})
    )

    default_option_space_gap = initial_oxygen_tanks_handle.background.get_height()

    # Tamanho do mapa

    map_size_y = initial_option_y + default_option_space_gap + space_between_options
    map_size_handle = Text(
      (center_x - 60, map_size_y),
      "Tamanho do mapa:",
      24,
      "white",
      (0, -2),
      background_file_name=["small_banner.png"],
      background_scale_by_size=(1.6, 1.5)
    )

    map_size_counter = Counter(
      (center_x + 105, map_size_y),

      15, 30, 15, self.shared_state["map_size"],

      24,
      "black",
      (0, -2),

      ["horizontal_strip.png"],
      ["buttons", "decrease.png"],
      ["buttons", "increase.png"],

      (40, 0),

      scale_by_size=(3, 3),
      button_sprite_size=(10, 10),
      button_disable_sprite_index=2,
      on_click=lambda new_size: self.shared_state.update({"map_size": new_size})
    )

    # Quantidade de jogadores

    player_count_y = initial_option_y + default_option_space_gap * 2 + space_between_options * 2
    player_count_handle = Text(
      (center_x - 60, player_count_y),
      "Jogadores:",
      24,
      "white",
      text_offset=(0, -2),
      background_file_name=["small_banner.png"],
      background_scale_by_size=(1.6, 1.5)
    )

    player_count_counter = Counter(
      (center_x + 105, player_count_y),

      2, 4, 1, self.shared_state["player_count"],

      24,
      "black",
      (0, -2),

      ["horizontal_strip.png"],
      ["buttons", "decrease.png"],
      ["buttons", "increase.png"],

      (40, 0),

      scale_by_size=(3, 3),
      button_sprite_size=(10, 10),
      button_disable_sprite_index=2,
      on_click=lambda new_count: self.shared_state.update({"player_count": new_count})
    )

    # Dificuldade

    difficulty_y = initial_option_y + default_option_space_gap * 3 + space_between_options * 3
    difficulty_handle = Text(
      (center_x - 60, difficulty_y),
      "Dificuldade:",
      24,
      "white",
      (0, -2),
      background_file_name=["small_banner.png"],
      background_scale_by_size=(1.6, 1.5)
    )

    difficulty_dropdown = Dropdown(
      (center_x + 105, difficulty_y),
      SpriteSource(
        ["buttons", "dropdown.png"],
        (48, 16),
        (2, 2)
      ),
      ["Fácil", "Médio", "Difícil"],
      self.shared_state["difficulty"],
      24,
      "black",
      option_text_offset=(-1, -1),
      on_click=lambda new_difficulty_index: self.shared_state.update({"difficulty": new_difficulty_index})
    )

    # Começar e sair

    def stop_game():
      self.game.running = False

    def start_game():
      self.manager.add_scene(PlayScene(self.shared_state))


    start_button_y = initial_option_y + default_option_space_gap * 4 + space_between_options * 5

    start_button = SpriteButton(
      (center_x, start_button_y),
      SpriteSource(
        ["buttons", "long_start.png"],
        (128, 26),
        (2.5, 2.5),
      ),
      on_click=lambda _: start_game()
    )

    quit_button_y = start_button_y + start_button.sprite_rect.height + space_between_options
    quit_button = SpriteButton(
      (center_x, quit_button_y),
      SpriteSource(
        ["buttons", "long_quit.png"],
        (128, 26),
        (2.5, 2.5),
      ),
      on_click=lambda _: stop_game()
    )

    on_sprite_source = SpriteSource(
      ["buttons", "on_soundtrack_toggle.png"],
      (26, 26),
      (2, 2),
    )

    off_sprite_source = SpriteSource(
      ["buttons", "off_soundtrack_toggle.png"],
      (26, 26),
      (2, 2),
    )

    real_sprite_width, real_sprite_height = on_sprite_source.real_sprite_size
    soundtrack_corner_gap = 5
    soundtrack_toggle = SoundtrackToggle(
      (real_sprite_width / 2 + soundtrack_corner_gap, window_height - real_sprite_height / 2 - soundtrack_corner_gap),
      on_sprite_source,
      off_sprite_source,
      self.manager
    )

    self.component_manager.add_components(
      game_title,
      initial_oxygen_tanks_handle,
      initial_oxygen_tanks_counter,
      map_size_handle,
      map_size_counter,
      player_count_handle,
      player_count_counter,
      difficulty_handle,
      start_button,
      quit_button,
      difficulty_dropdown, # Dropdown adicionado depois, pois ele vai ficar em cima do botão
      soundtrack_toggle
    )

  # A renderização foi separada de dentro da classe de ComponentManager
  # para ter um controle mais granulado a cerca da hierarquia de rende
  # rização.
  def draw(self):
    super().draw()
    drawable_background = self.background.copy()
    self.component_manager.draw_all(drawable_background)
    # Coloca toda a cena no fundo
    self.screen.blit(drawable_background, (0, 0))
