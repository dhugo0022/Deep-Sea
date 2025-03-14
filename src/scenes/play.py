from scene import Scene
from typing import Dict
from logic import get_difficulty_by_index
from libs.utils import load_image
from libs.components import SpriteSource, Text, Image, Timer, Alignment, SpriteButton
from libs.game_components import Map, PlayerBoard, SoundtrackToggle, FirstPlayerSorter, Submarine, DiceRoller, PlayerDecision, SubmarineOptions, WinnerDisplay
import pygame

class PlayScene(Scene):

  def __init__(self, shared_state: Dict[str, str]):
    super().__init__("play", shared_state, ["soundtracks", "cleyton_rx_underwater.ogg"])

  def setup(self):
    self.game.configure_game(
      self.shared_state["initial_oxygen_tanks"],
      self.shared_state["map_size"],
      self.shared_state["player_count"],
      get_difficulty_by_index(self.shared_state["difficulty"])
    )
    self.game.populate_map()

    window_width, window_height = pygame.display.get_window_size()
    self.background = load_image("background.png")
    self.background = pygame.transform.scale(self.background, (window_width, window_height))

    submarine_sprite = SpriteSource(
      ["entities", "submarine.png"],
      (64, 32),
      disabled_sprite_index=6
    )

    # A tela do jogo vai pegar 75% da tela e os outros 25%
    # vai ser responsável pela barra de status do jogo
    playable_game_width = window_width * 0.75
    sidebar_game_width = window_width - playable_game_width

    # Altura:
    # self.submarine_animation_height = window_height * 0.10
    self.submarine_animation_height = submarine_sprite.get_real_sprite_height()
    playable_game_height = window_height - self.submarine_animation_height
    sidebar_game_height = window_height

    map_sprite_size = 30
    map_gap_size = 2

    smallest_dimension = playable_game_height if playable_game_width > playable_game_height else playable_game_width
    # Equação criada para calcular o tamanho de escala necessária a partir da tela:
    # sb = [ss - g(tc - 1)]/(S*tc)
    # Onde:
    # - S("size") = largura do pixel;
    # - sb("scale_by") = tamanho da escala;
    # - ss("smallest dimension") = menor dimensão;
    # - tc("tile_count") = quantidade de quadrados;
    # - g("gap") = espaço entre quadrados
    scale_by_fit = (smallest_dimension - map_gap_size * (self.game.map_size - 1) ) / (map_sprite_size * self.game.map_size)

    self.game_map = Map(
      ((window_width / 2) - (sidebar_game_width / 2), (window_height / 2) + (self.submarine_animation_height / 2)),
      SpriteSource(
        ["map_tile.png"],
        (map_sprite_size, map_sprite_size),
        (scale_by_fit, scale_by_fit),
      ),
      SpriteSource(
        ["selected_map_tile.png"],
        (map_sprite_size, map_sprite_size),
        (scale_by_fit, scale_by_fit),
      ),
      SpriteSource(
        ["entities", "divers.png"],
        (24, 39),
      ),
      self.game,
      map_gap_size
    )

    game_map_width, _ = self.game_map.get_map_size()
    game_map_x, _ = self.game_map.position

    # Submarino

    self.submarine = Submarine(
      ((game_map_x - (game_map_width / 2)), self.submarine_animation_height / 2),
      submarine_sprite,
      game_map_x,
      game_map_width,
      self.game
    )

    # Barra de lado

    sidebar_centralized_x = playable_game_width + (sidebar_game_width / 2)
    sidebar_centralized_y = sidebar_game_height / 2

    sidebar_original_width = 360
    sidebar_original_height = 1080

    sidebar_width_proportionality_coefficient = sidebar_game_width / sidebar_original_width
    sidebar_height_proportionality_coefficient = sidebar_game_height / sidebar_original_height

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

    corner_button_gap = 5

    real_on_sprite_width, real_on_sprite_height = on_sprite_source.real_sprite_size
    soundtrack_toggle = SoundtrackToggle(
      (real_on_sprite_width / 2 + corner_button_gap, window_height - real_on_sprite_height / 2 - corner_button_gap),
      on_sprite_source,
      off_sprite_source,
      self.manager
    )

    def stop_game():
      self.game.running = False

    quit_sprite_source = SpriteSource(
      ["buttons", "quit.png"],
      (64, 26),
      (1.5, 1.5),
    )

    quit_sprite_width, quit_sprite_height = quit_sprite_source.real_sprite_size

    quit_button = SpriteButton(
      (quit_sprite_width / 2 + corner_button_gap, quit_sprite_height / 2 + corner_button_gap),
      quit_sprite_source,
      on_click=lambda _: stop_game()
    )

    sidebar = Image(
      (sidebar_centralized_x, sidebar_centralized_y),
      # Não vou especificar um tamanho para o sprite dele porque não
      # quero que ele seja tratado com uma spritesheet
      SpriteSource(
        ["sidebar_banner.png"],
        scale_by_size=(sidebar_width_proportionality_coefficient * 0.90, sidebar_height_proportionality_coefficient * 0.90)
      ),
    )

    initial_status_y = self.submarine_animation_height + 10

    status_title = Text(
      (sidebar_centralized_x, initial_status_y),
      "Status",
      36,
      "white",
      background_file_name=["small_banner.png"],
      background_scale_by_size=(1.6, 1.5)
    )

    info_left_x = sidebar_centralized_x - 120
    info_start_y = initial_status_y + 50
    space_between_info = 45
    horizontal_gap = 5

    # Temporizador

    timer_icon = Image(
      (info_left_x, info_start_y),
      SpriteSource(
        ["stopwatch.png"],
      ),
      alignment=Alignment.LEFT
    )

    timer_handle = Text(
      (horizontal_gap + timer_icon.get_x_position() + timer_icon.sprite_source.get_real_sprite_width(), timer_icon.get_y_position()),
      "Tempo:",
      28,
      "white",
      alignment=Alignment.LEFT
    )

    timer_value = Timer(
      (horizontal_gap + timer_handle.get_x_position() + timer_handle.text_object.get_width(), timer_handle.get_y_position()),
      timer_handle.text_size,
      timer_handle.text_color,
      alignment=Alignment.LEFT
    )

    # Oxigênio

    oxygen_tanks_icon = Image(
      (info_left_x, info_start_y + space_between_info),
      SpriteSource(
        ["oxygen_tank.png"],
      ),
      alignment=Alignment.LEFT
    )

    oxygen_tanks_handle = Text(
      (horizontal_gap + oxygen_tanks_icon.get_x_position() + oxygen_tanks_icon.sprite_source.get_real_sprite_width(), oxygen_tanks_icon.get_y_position()),
      "Oxigênio:",
      28,
      "white",
      alignment=Alignment.LEFT
    )

    self.oxygen_tanks_count = Text(
      (horizontal_gap + oxygen_tanks_handle.get_x_position() + oxygen_tanks_handle.text_object.get_width(), oxygen_tanks_handle.get_y_position()),
      f"{self.shared_state["initial_oxygen_tanks"]}",
      timer_handle.text_size,
      timer_handle.text_color,
      alignment=Alignment.LEFT
    )

    # Turnos

    turn_counter_icon = Image(
      (info_left_x, info_start_y + 2 * space_between_info),
      SpriteSource(
        ["turn_counter.png"],
      ),
      alignment=Alignment.LEFT
    )

    turn_counter_handle = Text(
      (horizontal_gap + turn_counter_icon.get_x_position() + turn_counter_icon.sprite_source.get_real_sprite_width(), turn_counter_icon.get_y_position()),
      "Turno:",
      28,
      "white",
      alignment=Alignment.LEFT
    )

    self.turn_counter_value = Text(
      (horizontal_gap + turn_counter_handle.get_x_position() + turn_counter_handle.text_object.get_width(), turn_counter_handle.get_y_position()),
      f"{self.game.turn}º",
      28,
      "white",
      alignment=Alignment.LEFT
    )

    # Jogadores

    profile_icon = Image(
      (info_left_x, info_start_y + 3 * space_between_info),
      SpriteSource(
        ["profile.png"],
      ),
      alignment=Alignment.LEFT
    )

    profile_handle = Text(
      (horizontal_gap + profile_icon.get_x_position() + profile_icon.sprite_source.get_real_sprite_width(), profile_icon.get_y_position()),
      "Jogadores:",
      28,
      "white",
      alignment=Alignment.LEFT
    )

    self.first_player_sorter = FirstPlayerSorter(
      (window_width // 2, window_height // 2),
      self.game
    )

    self.dice_roller = DiceRoller(
      (status_title.get_x_position(), turn_counter_icon.get_y_position() - 20),
      self.game
    )

    self.player_decision = PlayerDecision(
      (window_width // 2, window_height // 2),
      self.game
    )

    self.submarine_options = SubmarineOptions(
      (window_width // 2, window_height // 2),
      self.game
    )

    self.winner_display = WinnerDisplay(
      (window_width // 2, window_height // 2),
      self.game
    )

    # Registro de componentes

    self.component_manager.add_components(
      self.game_map,
      self.submarine,
      soundtrack_toggle,
      quit_button,
      sidebar,
      status_title,
      timer_icon,
      timer_handle,
      timer_value,
      oxygen_tanks_icon,
      oxygen_tanks_handle,
      self.oxygen_tanks_count,
      turn_counter_icon,
      turn_counter_handle,
      self.turn_counter_value,
      profile_icon,
      profile_handle,
      self.first_player_sorter,
      self.dice_roller,
      self.player_decision,
      self.submarine_options,
      self.winner_display
    )

    # Scoreboard

    player_board_source = SpriteSource(
      ["divers_info.png"],
      (144, 64),
      (1.5, 1.4),
      disabled_sprite_index=4
    )

    player_board_y = profile_icon.get_y_position() + profile_icon.sprite_source.get_real_sprite_height() + space_between_info

    for index, player in enumerate(self.game.players):
      player_board = PlayerBoard(
        (info_left_x, player_board_y + (index * space_between_info / 4) + (index * player_board_source.get_real_sprite_height())),
        player_board_source,
        player,
        self.game,
        alignment=Alignment.LEFT
      )

      self.component_manager.add_component(player_board)

  def draw(self):
    super().draw()
    drawable_background = self.background.copy()
    # Atualiza o texto com a quantidade restante de oxygênio
    self.oxygen_tanks_count.text = f"{self.game.oxygen_tanks}"
    self.turn_counter_value.text = f"{self.game.turn}º"
    # Desenha os componentes na superfície que vai ser "blitada" na tela no final
    self.component_manager.draw_all(drawable_background)
    # Coloca toda a cena no fundo
    self.screen.blit(drawable_background, (0, 0))
