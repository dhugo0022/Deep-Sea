import pygame
from libs.utils import clip_sprites, get_font, load_image, load_sound, MOUSE_LEFT_BUTTON, sum_tuples, multiply_tuple_by_scalar
from typing import Callable, Union
import sys
from enum import Enum
from timeit import default_timer as timer
import math

class Alignment(Enum):
  LEFT = 0,
  CENTER = 1,
  RIGHT = 2

def align_rect(rect: pygame.Rect, alignment: Alignment, position: tuple[int, int]):
    x, y = position

    match alignment:
      case Alignment.LEFT:
        rect.left = x
      case Alignment.CENTER:
        rect.centerx = x
      case Alignment.RIGHT:
        align_rect.right = x

    rect.centery = y

# Une três tipos diferente em um único type-checking
SpriteInput = Union[list[str], pygame.Surface, list[pygame.Surface]]

class SpriteSourceType(Enum):
  SURFACE_SPRITE = 0, # Caso seja passado só uma Surface
  PATH_SPRITE = 1, # Caso seja passado uma list[str] e o sprite_size não tenha sido especificado
  SURFACE_SPRITE_LIST = 2, # Caso seja passado uma list[Surface]
  PATH_SPRITE_LIST = 3 # Caso seja passado uma list[str] e o sprite_size tenha sido especificado

class SpriteSource():
  """
    Uma sprite source é:\n
    - Uma imagem ou sprites(se o tamanho do sprite for especificado)
      a partir do caminho pra um arquivo, caso seja uma lista de strings;\n
    - A própria imagem, caso seja uma Surface;\n
    - Um conjunto de sprites(onde o tamanho do sprite é inferido a
      partir do primeiro item da lista) caso seja uma lista de Surface.\n
  """
  def __init__(
      self,
      source: SpriteInput,

      sprite_size: tuple[int, int] = None,
      scale_by_size: tuple[int, int] = None,
      disabled_sprite_index: int = None,
  ):
    self.source = source
    self.sprite_size = sprite_size
    self.scale_by_size = scale_by_size

    self.disabled_sprite_index = disabled_sprite_index

    self.sprites: list[pygame.Surface] = []

    if type(source) == pygame.Surface:
      self.sprites.append(source if not self.has_scale_by_size() else pygame.transform.scale_by(source, self.scale_by_size))
      self.source_type = SpriteSourceType.SURFACE_SPRITE
      self.sprite_count = len(self.sprites)

    elif type(source) == list:
      if len(source) < 1:
        sys.exit(f"A lista para a SpriteSource está vazia: {self.source}")
        return

      # TODO: checar se todos os items da lista são do mesmo tipo para previnir possíveis erros de uso
      list_type = type(source[0])

      if not list_type == pygame.Surface and not list_type == str:
        sys.exit(f"Tipo de entrada inválido para uma lista da SpriteSource, tipo: {list_type}. Em: {self.source}")
        return

      # Lista de surfaces
      if list_type == pygame.Surface:

        if self.has_scale_by_size():
          self.sprites = [pygame.transform.scale_by(sprite, scale_by_size) for sprite in source[:]]
        else:
          self.sprites = source[:] # Shallow copy

        self.source_type = SpriteSourceType.SURFACE_SPRITE_LIST

      # Lista com strings que se refere a um diretório
      elif list_type == str:
        temp_image = load_image(*source)

        if self.has_sprite_size():
          self.sprites = clip_sprites(temp_image, sprite_size, scale_by_size)
          self.source_type = SpriteSourceType.PATH_SPRITE_LIST
        else:
          self.sprites.append(temp_image if not self.has_scale_by_size() else pygame.transform.scale_by(temp_image, self.scale_by_size))
          self.source_type = SpriteSourceType.PATH_SPRITE

    if self.has_disabled_sprite():
      if len(self.sprites) < 2:
        sys.exit(f"A lista de sprites é muito pequena(menor que 2) para ter um sprite de desativado: {self.source}")
        return

      if 0 > self.disabled_sprite_index > len(source) - 1:
        sys.exit(f"O índice do sprite de desativado não pode ser menor que 0 ou maior que o maior índice da lista de fonte: {self.source}")
        return

      self.disabled_sprite = self.sprites.pop(self.disabled_sprite_index)

    # Pega o tamanho real do sprite caso ele seja redimensionado
    self.real_sprite_size = self.first_sprite().get_size()

    # Coloca a contagem de sprites que vai ser utilizada para
    # iterar em loops para não ter chamar a função "len()"
    # de forma repetida
    self.sprite_count = len(self.sprites)

  def first_sprite(self):
    return self.sprites[0]

  def get_sprite_width(self):
    return self.sprite_size[0]

  def get_sprite_height(self):
    return self.sprite_size[1]

  def get_real_sprite_width(self):
    return self.real_sprite_size[0]

  def get_real_sprite_height(self):
    return self.real_sprite_size[1]

  def has_scale_by_size(self):
    return self.scale_by_size is not None

  def has_disabled_sprite(self):
    return self.disabled_sprite_index is not None

  def has_sprite_size(self):
    return self.sprite_size is not None

  def has_multiple_sprites(self):
    return self.source_type == SpriteSourceType.SURFACE_SPRITE_LIST or self.source_type == SpriteSourceType.PATH_SPRITE_LIST

  def generate_sprite_rect(
      self,
      position: tuple[int, int],
      sprite_index: int = 0,
      alignment: Alignment = Alignment.CENTER
    ) -> pygame.Rect:
    """
      Gera um retângulo que engobla todo o sprite específicado.\n
      O centro retângulo gerado por esse sprite é colocado\n
      na posiçao especificada.
    """
    if 0 > sprite_index > self.sprite_count:
      sys.exit(f"O índice do sprite não pode ser menor que 0 ou maior que o maior índice da lista de sprites: {self.source}")
      return

    sprite = self.sprites[sprite_index]
    sprite_rect = sprite.get_rect()
    align_rect(sprite_rect, alignment, position)

    return sprite_rect

# Essa notação de tipo: Callable[[pygame.event.Event], None].
# Indica que a variável vai ter um lambda que vai utilizar
# um objeto do tipo pygame.event.Event como argumento e
# vai retornar um None (void).
class Component():
  """
    Classe base principal para todos os outros componentes.
  """
  def __init__(self,
    position: tuple[int, int],
    alignment: Alignment = Alignment.CENTER,
    on_click: Callable[[any], None] = None,
    on_hover: Callable[[any], None] = None,
  ):
    # Elas não vão ser definidas diretamente no escopo da classe por conta
    # da maneira de funcionamento das classes. Caso elas seja definidas fora
    # elas podem compartilhar estado com outras instâncias e isso pode dar
    # problemas de funcionalidade
    self._expanded = False
    self._expandable = False
    self._interactable = False
    self._animated = False
    self.disabled = False

    self.position = position
    self.alignment = alignment
    self.on_click = on_click
    self.on_hover = on_hover
    self.pressed = False
    self.hovered = False

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]) -> bool:
    """
      Verifica se o par ordenado que sere refere à posição do\n
      mouse pertence ao domínio formado pelos possíveis pares\n
      ordenados(x, y) que estão contidos nas áreas clicáveis do\n
      componente.
    """
    return False

  def listen(self, event: pygame.event.Event):
    """
      Funcão utilizada para gerenciar eventos que se\n
      referem ao componente.
    """
    pass

  def draw(self, screen: pygame.Surface):
    """
      Funcão utilizada para desenhar o componente na\n
      tela do jogo.
    """
    pass

  def animate(self, animation_reset: bool = False):
    pass

  def get_x_position(self):
    return self.position[0]

  def get_y_position(self):
    return self.position[1]

  @property
  def expanded(self) -> bool:
    return self._expanded

  @property
  def expandable(self) -> bool:
    return self._expandable

  @property
  def interactable(self) -> bool:
    return self._interactable

  @property
  def animated(self) -> bool:
    return self._animated


class ComponentManager:
  """
    Gerenciador de componentes responsável por gerenciar todos\n
    os componentes de uma cena. Essa classe é também responsável\n
    por cuidar da hierarquia de clicks.
  """
  def __init__(self):
    self._components: list[Component] = []

  @property
  def components(self) -> list[Component]:
    return self._components

  def add_component(self, component: Component):
    self._components.append(component)

  def add_components(self, *components: Component):
    for component in components:
      self.add_component(component)

  def remove_component(self, component_or_index: Union[int, Component]):
    variable_type = type(component_or_index)
    if variable_type == Component:
      self._components.remove(component_or_index)
    elif variable_type == int:
      self._components.pop(component_or_index)
    else:
      sys.exit(f"A função de remoção não suporta o tipo especificado: {variable_type}.")

  def draw_all(self, screen: pygame.Surface):
    for component in self._components:
      component.draw(screen)

  def __filter_all_mouse_interacted_components(self, mouse_pos: tuple[int, int]) -> list[tuple[int, Component]]:
    return [(index, component) for index, component in enumerate(self._components) if component.is_mouse_within_bounding_box(mouse_pos) and not component.disabled]

  def __is_component_at_least_interacting(self, component: Component, mouse_interacted_components: list[tuple[int, Component]]):
    return any(component == interacted_component for _, interacted_component in mouse_interacted_components)

  def __filter_highest_interacted_component_at_mouse_pos(self, mouse_interacted_components: list[tuple[int, Component]]) -> Component:
    if len(mouse_interacted_components) < 1:
      return None

    if len(mouse_interacted_components) == 1:
      return mouse_interacted_components.pop()[1] # Pega só o componente

    max_index = max(index for index, _ in mouse_interacted_components)
    highest_component_filter = [component for index, component in mouse_interacted_components if index == max_index]
    highest_component = highest_component_filter.pop()

    return highest_component

  def listen(self, events: list[pygame.event.Event]):
    for component in self._components:
      for event in events:
        # Se o componente não for interativo(há a possibilidade de haver click), só pula a iteração
        if not component.interactable:
          continue

        # TODO: adicionar o sistema de componente desativado para todos os componentes(não só botões) e pular iteração caso eles estejam desativado
        # Cuida da hierarquia dos clicks e previne um botão que esteja
        # debaixo de outro, que esteja em foco, seja clicado.
        mouse_interacted_components = self.__filter_all_mouse_interacted_components(pygame.mouse.get_pos())

        # Isso permite que componentes interativos que não estejam em área de click
        # tenha seus estados atualizados também.
        if not self.__is_component_at_least_interacting(component, mouse_interacted_components):
          component.listen(event)

        highest_interacted_component = self.__filter_highest_interacted_component_at_mouse_pos(mouse_interacted_components)

        if highest_interacted_component == component:
          component.listen(event)

        component.animate(animation_reset = not highest_interacted_component == component)


# TODO: calcular a fonte a ser usada a partir da resolução de tela
# TODO: implementar click para o componente de texto
class Text(Component):
  """
    Criar um texto na tela que pode atualizado diretamente.
  """
  def __init__(self,
    position: tuple[int, int],

    text: str,
    text_size: int,
    text_color: pygame.Color,
    text_offset: tuple[int, int] = None,
    alignment: Alignment = Alignment.CENTER,

    background_file_name: list[str] = None,
    background_scale_by_size: tuple[int, int] = None,
  ):
    super().__init__(position, alignment)
    self._text = text
    self.text_size = text_size
    self.text_color = text_color
    self._text_offset = text_offset

    self.background_file_name = background_file_name
    self.background_scale_by_size = background_scale_by_size

    self.__setup()

  def __has_background(self):
    return self.background_file_name is not None

  def __has_background_scale_by_size(self):
    return self.background_scale_by_size is not None

  def __has_text_offset(self):
    return self._text_offset is not None

  def __setup(self):
    self.text_object = get_font(self.text_size).render(self._text, 1, self.text_color)
    self.text_object_rect = self.text_object.get_rect()

    align_rect(self.text_object_rect, self.alignment, self.position)

    if self.__has_text_offset():
      # O map performa uma operação entre os itens das tuplas
      # e retorna uma nova tupla com as operações feitas
      self.text_object_rect.center = sum_tuples(self.text_object_rect.center, self._text_offset)

    if self.__has_background():

      # Coloca o fundo do objeto no tamanho especificado e
      # deixa o meio do retângulo dele no mesmo lugar da
      # posição informada pelo constructor da classe
      self.background = load_image(*self.background_file_name)

      if self.__has_background_scale_by_size():
        self.background = pygame.transform.scale_by(self.background, self.background_scale_by_size)

      self.background_rect = self.background.get_rect()
      align_rect(self.background_rect, self.alignment, self.position)

  # Decorators de propriedade que permitem ter uma
  # funcionalidade specífica de manipular a ação de
  # quando uma variável é acessada, modificada ou
  # deletada.
  @property
  def text(self):
    return self._text

  # Se quiséssemos suportar a mudança do texto ao longo da
  # renderização do texto no jogo, nós teriamos que criar
  # um objeto de fonte na função de "draw()" para que o
  # objeto de texto seja atualizado com o novo texto, mas
  # isso criaria um objeto 60 vezes em 1 segundo (60 fps).
  # Para não ter que gerar um objeto de fonte novo tantas
  # vezes, nós podemos usar um decorator de propriedade
  # para verificar as vezes que o texto muda e atualizar
  # o objeto de texto com o novo texto a partir disso.
  @text.setter
  def text(self, new_text: str):
    self._text = new_text
    self.__setup()


  @property
  def text_offset(self):
    return self._text_offset

  @text_offset.setter
  def text_offset(self, new_text_offset: tuple[int, int]):
    self._text_offset = new_text_offset
    self.__setup()

  def draw(self, screen: pygame.surface.Surface):
    if self.__has_background():
      screen.blit(self.background, self.background_rect.topleft)
    screen.blit(self.text_object, self.text_object_rect.topleft)


class SpriteButton(Component):
  """
    Cria um botão animado automaticamente, a partir de uma spritesheet.
  """
  def __init__(
    self,
    position: tuple[int, int],
    sprite_source: SpriteSource,
    disabled: bool = False,
    alignment: Alignment = Alignment.CENTER,
    on_click: Callable[[pygame.event.Event], None] = None,
    on_hover: Callable[[pygame.event.Event], None] = None,
  ):
    super().__init__(position, alignment, on_click, on_hover)
    self._interactable = True
    self._animated = True
    # Lógica específica do botão
    self.clicked_up = False

    self.sprite_source = sprite_source
    self.sprite_rect = self.sprite_source.generate_sprite_rect(self.position, alignment=self.alignment)
    # Pega a terceira parte da divisão do número de sprites
    # fazer as animações
    self.sprite_third = round(self.sprite_source.sprite_count / 3)
    # Índice que vai ser utilizado para escolher o sprite que vai ser
    # renderizado na tela
    self.sprite_index = 0

    self._disabled = disabled

    # Carrega os sons do botão
    self.button_click_start_sound = load_sound("components", "button_click_start.ogg")
    self.button_click_end_sound = load_sound("components", "button_click_end.ogg")

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.sprite_rect.collidepoint(mouse_pos)

  def draw(self, screen: pygame.surface.Surface):
    # Renderiza o botão na tela, tendo o seu meio
    # posto como a posição passada no argumento
    # de posição do botão
    sprite = None
    if self.sprite_source.has_multiple_sprites():
      # Usa o sprite de botão desativado caso ele
      # esteja desativado e tenha um sprite de botão
      # desativado configurado
      sprite = self.sprite_source.disabled_sprite if self.sprite_source.has_disabled_sprite() and self.disabled else self.sprite_source.sprites[self.sprite_index]
    else:
      sprite = self.sprite_source.first_sprite()

    screen.blit(sprite, self.sprite_rect.topleft)

  def listen(self, event: pygame.event.Event):
    # Se o botão estiver clicado ou desativado só pula até
    # ele poder ser clicável novamente.
    if self.disabled:
      return

    # if self.clicked_up and self.sprite_source.has_multiple_sprites():
    #   return

    if event.type == pygame.MOUSEMOTION:
      # Executa a função de callback on_hover quando o mouse passa por cima
      if self.on_hover and self.hovered:
        self.on_hover(event)

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_LEFT_BUTTON:
      self.pressed = self.is_mouse_within_bounding_box(event.pos)
      if self.pressed:
        self.button_click_start_sound.play()
    elif event.type == pygame.MOUSEBUTTONUP and event.button == MOUSE_LEFT_BUTTON:

      # Processa o click do usuário caso ele esteja com condições para tal
      if self.pressed:
        self.pressed = False

        if self.sprite_source.has_multiple_sprites():
          # Quando o botão foi confirmado (ele soltou o botão)
          # nós colocamos ele em estado de clicado para realizar
          # as animações de click de volta de forma flúida
          self.clicked_up = True

        # O click só é confirmado caso o player solte o click
        # enquanto ainda estiver nas redondezas do botão
        if self.is_mouse_within_bounding_box(event.pos):
          self.button_click_end_sound.play()

          if self.on_click:
            self.on_click(event)

  def animate(self, animation_reset: bool = False):
    # Se o mouse está em cima do botão
    self.hovered = self.is_mouse_within_bounding_box(pygame.mouse.get_pos())

    if not self._animated or not self.sprite_source.has_multiple_sprites():
      return

    if self.disabled:
      if self.sprite_index > 0:
        self.sprite_index = 0 # Reseta o índice do sprite da animação
        self.clicked_up = False
      return

    # TODO: deixar esse código mais compacto
    if self.clicked_up:
      # Quando o botão clicado foi solto, mas o mouse ainda está em cima do botão

      if self.hovered:
        compared_range = 0 if self.sprite_source.sprite_count == 2 else (self.sprite_source.sprite_count - self.sprite_third * 2)

        if self.sprite_index > compared_range:
          self.sprite_index -= 1

          if self.sprite_index == compared_range:
            self.clicked_up = False
      # Quando o botão clicado foi solto, mas o mouse não está mais em cima do botão
      else:
        if self.sprite_index > 0:
          self.sprite_index -= 1

          if self.sprite_index == 0:
            self.clicked_up = False

    # Quando há sprites e o botão clicado não foi solto
    else:
      # Se não tiver com o mouse em cima e nem pressionado
      if not self.hovered and not self.pressed and self.sprite_index > 0:
        self.sprite_index -= 1
        return

      # Se ele estiver em modo de reset de animação, ele não vai mudar para a animação de click
      if animation_reset:
        return

      # Aumenta o índice de iteração dos sprites
      if self.hovered:
        if self.pressed:
          if self.sprite_source.sprite_count == 2:
            self.sprite_index = 1
            return

          if (self.sprite_source.sprite_count - self.sprite_third * 2) <= self.sprite_index < (self.sprite_source.sprite_count - 1):
            self.sprite_index += 1
        else:
          if (self.sprite_source.sprite_count > 2 and self.hovered and not self.pressed):
            if 0 <= self.sprite_index < (self.sprite_source.sprite_count - self.sprite_third * 2):
              self.sprite_index += 1



# TODO: atualizar a classe para usar o SpriteSource diretamente
class Counter(Component):
  """
    Criar um contador que é atualizado manualmente
  """
  def __init__(
    self,
    position: tuple[int, int],

    min_value: int,
    max_value: int,
    step_value: int,
    starting_value: int,

    text_size: int,
    text_color: pygame.Color,
    text_offset: tuple[int, int],

    display_file_name: list[str],
    decrease_button_file_name: list[str],
    increase_button_file_name: list[str],

    button_offset: tuple[int, int],

    alignment: Alignment = Alignment.CENTER,
    scale_by_size: tuple[int, int] = None,
    button_sprite_size: tuple[int, int] = None,
    button_disable_sprite_index: tuple[int, int] = None,

    on_click: Callable[[int], None] = None
  ):
    super().__init__(position, on_click=on_click)
    self._interactable = True

    self.min_value = min_value
    self.max_value = max_value
    self.step_value = step_value

    self.starting_value = starting_value

    if self.min_value > starting_value > self.max_value:
      sys.exit("O valor de início não pode ser menos que o valor mínimo e nem maior que o valor máximo.")
      return

    if self.min_value > self.max_value:
      sys.exit("O valor mínimo não pode ser maior que o valor máximo.")
      return

    self.count = starting_value

    self.text = Text(
      position,
      str(self.starting_value),
      text_size,
      text_color,
      text_offset,
      alignment,
      background_file_name=display_file_name,
      background_scale_by_size=scale_by_size
    )

    def toggle_counter(increase: bool = False):
      if self.count == (self.max_value if increase else self.min_value):
        return

      if increase:
        self.count = min(self.count + self.step_value, self.max_value)
      else:
        self.count = max(self.count - self.step_value, self.min_value)

      self.text.text = str(self.count)

      self.decrease_button.disabled = self.count == self.min_value
      self.increase_button.disabled = self.count == self.max_value

      if self.on_click:
        self.on_click(self.count)

    self.decrease_button = SpriteButton(
      sum_tuples(position, multiply_tuple_by_scalar(button_offset, -1)),
      SpriteSource(
        decrease_button_file_name,
        button_sprite_size,
        scale_by_size,
        button_disable_sprite_index,
      ),
      self.count == self.min_value,
      alignment=alignment,
      on_click=lambda _: toggle_counter()
    )

    self.increase_button = SpriteButton(
      sum_tuples(position, button_offset),
      SpriteSource(
        increase_button_file_name,
        button_sprite_size,
        scale_by_size,
        button_disable_sprite_index
      ),
      self.count == self.max_value,
      alignment=alignment,
      on_click=lambda _: toggle_counter(True)
    )

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
    return self.decrease_button.is_mouse_within_bounding_box(mouse_pos) or self.increase_button.is_mouse_within_bounding_box(mouse_pos)

  def draw(self, screen: pygame.surface.Surface):
    self.text.draw(screen)
    self.decrease_button.draw(screen)
    self.increase_button.draw(screen)

  def listen(self, event):
    self.text.listen(event)
    self.decrease_button.listen(event)
    self.increase_button.listen(event)

  def animate(self, animation_reset: bool = False):
    # self.text.animate(animation_reset) # Text não é animado atualmente (23/11/2024)
    self.decrease_button.animate(animation_reset)
    self.increase_button.animate(animation_reset)

# TODO: Adicionar sistema de alinhamento
class Dropdown(Component):
  """
    Implementa um menu dropdown com itens pré-especificados.
  """
  def __init__(
    self,
    position: tuple[int, int],

    sprite_source: SpriteSource,
    items: list[str],
    selected_index: int,

    text_size: int,
    text_color: pygame.Color,
    text_offset: tuple[int, int] = None,
    option_text_offset: tuple[int, int] = None,

    on_click: Callable[[int], None] = None
  ):
    super().__init__(position, on_click=on_click)
    self._expandable = True
    self._interactable = True

    self.sprite_source = sprite_source
    self.items = items
    self.selected_index = selected_index

    self.text_size = text_size
    self.text_color = text_color
    self.text_offset = text_offset
    self.option_text_offset = option_text_offset

    if 0 > selected_index > len(items) - 1:
      sys.exit("O índice do item selecionado não pode ser menor que 0 ou maior que o maior índice da lista de items.")
      return

    if not self.sprite_source.sprite_count == 4:
      sys.exit("A quantidade de sprites em um dropdown tem que ser igual a quatro.")
      return

    self.__setup()

  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]):
      return self.decrease_button.is_mouse_within_bounding_box(mouse_pos) or self.increase_button.is_mouse_within_bounding_box(mouse_pos)

  def __has_text_offset(self):
    return self.text_offset is not None

  def __has_option_text_offset(self):
    return self.option_text_offset is not None

  # TODO: reescrever para usar um botão como implementação das opções de click
  def __setup(self):
    self.display_object = self.sprite_source.first_sprite()
    self.display_object_rect = self.display_object.get_rect()
    self.display_object_rect.center = self.position

    self.display_object_text = get_font(self.text_size).render(self.items[self.selected_index], 1, self.text_color)
    self.display_object_text_rect = self.display_object_text.get_rect()
    self.display_object_text_rect.center = self.position
    if self.__has_text_offset():
      self.display_object_text_rect.center = sum_tuples(self.display_object_text_rect.center, self.text_offset)

    self.options_objects: list[tuple[pygame.Surface, pygame.Rect, pygame.Surface, pygame.Rect]] = []
    for index, item in enumerate(self.items):
      _, sprite_height = self.sprite_source.real_sprite_size
      option_position_offset = (0, (index + 1) * sprite_height)
      option_position = sum_tuples(self.position, option_position_offset)

      option_object = self.sprite_source.sprites[2].copy()
      option_object_selected = self.sprite_source.sprites[3].copy()
      option_object_rect = option_object.get_rect()
      option_object_rect.center = option_position

      option_object_text = get_font(self.text_size).render(item, 1, self.text_color)
      option_object_text_rect = option_object_text.get_rect()
      option_object_text_rect.center = option_position
      if self.__has_option_text_offset():
        option_object_text_rect.center = sum_tuples(option_object_text_rect.center, self.option_text_offset)

      self.options_objects.append((index, option_object, option_object_selected, option_object_rect, option_object_text, option_object_text_rect))


  def is_mouse_within_bounding_box(self, mouse_pos: tuple[int, int]) -> bool:
    if self._expanded:
      return self.__is_mouse_within_bounds_of_display(mouse_pos) or self.__is_mouse_within_bounds_of_options(mouse_pos)[0]
    else:
      return self.__is_mouse_within_bounds_of_display(mouse_pos)

  def draw(self, screen: pygame.surface.Surface):
    screen.blit(self.display_object, self.display_object_rect.topleft)
    screen.blit(self.display_object_text, self.display_object_text_rect.topleft)

    is_hovered, hovered_index = self.__is_mouse_within_bounds_of_options(pygame.mouse.get_pos())
    if self._expanded:
      for index, option_object, option_object_selected, option_object_rect, option_object_text, option_object_text_rect in self.options_objects:
        screen.blit(option_object_selected if is_hovered and hovered_index == index else option_object, option_object_rect.topleft)
        screen.blit(option_object_text, option_object_text_rect.topleft)

  def __is_mouse_within_bounds_of_display(self, mouse_pos: tuple[int, int]) -> bool:
    return self.display_object_rect.collidepoint(mouse_pos)

  def __is_mouse_within_bounds_of_options(self, mouse_pos: tuple[int, int]) -> tuple[bool, int]:
    for index, _, _, option_object_rect, _, _ in self.options_objects:
      if option_object_rect.collidepoint(mouse_pos):
        return (True, index)
    return (False, -1)

  # TODO: adicionar animation reset no dropdown, para quando ele for animado
  def listen(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
      if self.__is_mouse_within_bounds_of_display(event.pos):
        self._expanded = not self._expanded

        self.display_object = self.sprite_source.sprites[1 if self._expanded else 0]
        return

      # A partir daqui, se o dropdown não tiver expandido
      # não há nada pra fazer
      if not self._expanded:
        return

      is_colliding, new_selected_index = self.__is_mouse_within_bounds_of_options(event.pos)

      if is_colliding: # Quando está colidindo
        # Quando está selecionado um valor já selecionado
        if self.selected_index == new_selected_index:
          return

        self.selected_index = new_selected_index

        new_value = self.items[new_selected_index]
        if self.on_click:
          self.on_click(new_selected_index)

        # Refaz o objeto de display de texto com a nova opção selecionada
        self.display_object_text = get_font(self.text_size).render(new_value, 1, self.text_color)
        self.display_object_text_rect = self.display_object_text.get_rect()
        self.display_object_text_rect.center = self.position
        if self.__has_text_offset():
          self.display_object_text_rect.center = sum_tuples(self.display_object_text_rect.center, self.text_offset)

        self._expanded = False
        self.display_object = self.sprite_source.sprites[1 if self._expanded else 0]

class Image(Component):
  """
    Uma imagem que pode ser clicada e possui uma opção de flip\n
    que muda a orientação.
  """
  def __init__(
    self,
    position: tuple[int, int],
    sprite_source: SpriteSource,
    alignment: Alignment = Alignment.CENTER,
    flip_rule: tuple[bool, bool] = None,
    on_click: Callable[[], None] = None
  ):
    super().__init__(position, alignment, on_click)
    self._interactable = True

    self.sprite_source = sprite_source

    self.use_flip = False
    self.flip_rule = flip_rule if flip_rule else (False, False)

    self.on_click = on_click
    self.__setup()

  def __setup(self):
    self.image_object_rect = self.sprite_source.generate_sprite_rect(self.position)
    align_rect(self.image_object_rect, self.alignment, self.position)

  def is_mouse_within_bounding_box(self, mouse_pos):
    return self.__is_mouse_within_bounds(mouse_pos)

  def move_by(self, x, y):
    self.image_object_rect.move_ip(x, y)
    self.position = self.image_object_rect.center
    align_rect(self.image_object_rect, self.alignment, self.position)

  def set_flip_rule(self, flip_x: bool, flip_y: bool):
    self.flip_rule = (flip_x, flip_y)

  def set_use_flip(self, use_flip):
    self.use_flip = use_flip

  def draw(self, screen):
    selected_sprite = self.sprite_source.first_sprite()
    drawn_sprite = pygame.transform.flip(selected_sprite, self.flip_rule[0], self.flip_rule[1]) if self.use_flip else selected_sprite
    screen.blit(drawn_sprite, self.image_object_rect.topleft)

  def __is_mouse_within_bounds(self, mouse_pos):
    return self.image_object_rect.collidepoint(mouse_pos)

  def listen(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == MOUSE_LEFT_BUTTON:
      self.pressed = self.__is_mouse_within_bounds(event.pos)
      if self.pressed and self.on_click:
        self.on_click()

class AnimatedImage(Image):
  """
    Cria uma animação, a partir da classe :py:class:`Image`, com sprites fornecidos.\n
    A animação será executada até que seja desativada.\n
    A animação será reiniciada automaticamente após completar uma volta.
  """
  def __init__(
    self,
    position: tuple[int, int],
    sprite_source: SpriteSource,
    alignment: Alignment = Alignment.CENTER,
    flip_rule: tuple[bool, bool] = None,
    on_click: Callable[[], None] = None
  ):
    super().__init__(position, sprite_source, alignment, flip_rule, on_click)
    self.sprite_index = 0
    self.disabled = False

  def draw(self, screen):
    if self.disabled:
      if self.sprite_source.has_disabled_sprite():
        screen.blit(self.sprite_source.disabled_sprite, self.image_object_rect.topleft)

      return

    selected_sprite = self.sprite_source.sprites[self.sprite_index]
    drawn_sprite = pygame.transform.flip(selected_sprite, self.flip_rule[0], self.flip_rule[1]) if self.use_flip else selected_sprite
    screen.blit(drawn_sprite, self.image_object_rect.topleft)
    if self.sprite_index < self.sprite_source.sprite_count - 1:
      self.sprite_index += 1
    else:
      self.sprite_index = 0

class Timer(Component):
  """
    Cria um timer que irá realizar uma contagem de 1 em 1 segundo\n
    a partir do 0.
  """
  def __init__(
    self,
    position: tuple[int, int],
    text_size: int,
    text_color: pygame.Color,
    text_offset: tuple[int, int] = None,
    alignment: Alignment = Alignment.CENTER,
  ):
    super().__init__(position, alignment)
    self.text_size = text_size
    self.text_color = text_color
    self.text_offset = text_offset

    self.text = Text(position, "", text_size, text_color, text_offset, alignment)
    self.initial_time = timer()

  def __format_seconds(self, time_in_seconds: float):
    sec = time_in_seconds % 60
    min = time_in_seconds // 60
    hr = min // 60
    day = hr // 24

    sec = math.trunc(sec)
    min = math.trunc(min % 60)
    hr = math.trunc(hr % 24)
    day = math.trunc(day)

    # Formata para o padrão "%Dd %Hh %Mm %Ss"
    formatted_str = ""
    if day > 0:
      formatted_str += f"{day}d "

    if hr > 0:
      formatted_str += f"{hr}h "

    if min > 0:
      formatted_str += f"{min}m "

    if sec >= 0:
      formatted_str += f"{sec}s "

    return formatted_str

  def draw(self, screen: pygame.Surface):
    current_time = timer()
    elapsed_time_in_seconds = current_time - self.initial_time
    self.text.text = self.__format_seconds(elapsed_time_in_seconds)
    self.text.draw(screen)
