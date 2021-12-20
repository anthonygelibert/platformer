#!/usr/bin/env python3.10
# coding=utf-8

""" Little game. """

from __future__ import annotations

import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import EX_OK
from pathlib import Path

import pygame
from dacite import Config, from_dict
from jsonschema.validators import validate
from pygame.font import Font
from pygame.surface import Surface, SurfaceType
from rich import print, traceback

GAME_NAME = "TLN Power"
WIDTH = 960
HEIGHT = 640
FPS = 60


class GameState(ABC):
    """ Game abstract state. """

    def __init__(self, game_engine: GameEngine, visual_engine: VisualEngine, music_engine: MusicEngine,
                 level_engine: LevelEngine) -> None:
        self.game_engine = game_engine
        self.visual_engine = visual_engine
        self.music_engine = music_engine
        self.level_engine = level_engine

    @abstractmethod
    def process_events(self) -> None:
        """ Process all the events (keys…). """
        pass

    @abstractmethod
    def update(self) -> None:
        """ Update internal state according to current state. """
        pass

    @abstractmethod
    def draw(self) -> None:
        """ Draw for the current state. """
        pass


class PlayingState(GameState):
    """ Game is playing. """

    def __init__(self, game_engine: GameEngine, visual_engine: VisualEngine, music_engine: MusicEngine,
                 level_engine: LevelEngine, level: int) -> None:
        super().__init__(game_engine, visual_engine, music_engine, level_engine)
        level = level_engine.load(f"world-{level}")

        music_engine.play_music(level.music)
        visual_engine.set_background(level.background_color, level.background_img)
        visual_engine.set_scenery(level.scenery_img)

        visual_engine.write_centered_text(level.name, visual_engine.FONT_MD, (0, 0, 0), (WIDTH // 2, 16))

    def process_events(self) -> None:
        """ Handle all keys. """
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT | pygame.KEYDOWN if event.key == pygame.K_q:
                    self.game_engine.done = True
                case pygame.KEYDOWN if event.key == pygame.K_SPACE:
                    print("Player jump")
                case pygame.KEYDOWN if event.key == pygame.K_LEFT:
                    print("Player left")
                case pygame.KEYDOWN if event.key == pygame.K_RIGHT:
                    print("Player right")
                case pygame.KEYDOWN if event.key == pygame.K_RIGHT:
                    print("Player right")


    def update(self) -> None:
        pass

    def draw(self) -> None:
        pass


class SplashScreenState(GameState):
    """ Splash screen. """

    def __init__(self, game_engine: GameEngine, visual_engine: VisualEngine, music_engine: MusicEngine,
                 level_engine: LevelEngine) -> None:
        super().__init__(game_engine, visual_engine, music_engine, level_engine)
        level = level_engine.load("splash")

        music_engine.play_music(level.music)
        visual_engine.set_background(level.background_color, level.background_img)
        visual_engine.set_scenery(level.scenery_img)

        first_line = visual_engine.write_centered_text(GAME_NAME, visual_engine.FONT_LG, (16, 86, 103),
                                                       (WIDTH // 2, HEIGHT // 3))
        visual_engine.write_centered_text("Appuie sur une touche", visual_engine.FONT_SM, (255, 255, 255),
                                          (WIDTH // 2, (HEIGHT // 3) + 16 + first_line.get_height()))

    def process_events(self) -> None:
        """ Wait for any key. """
        for event in pygame.event.get():
            print("splash: ", event)
            match event.type:
                case pygame.QUIT:
                    self.game_engine.done = True
                case pygame.KEYDOWN:
                    self.game_engine.current_state = PlayingState(self.game_engine, self.visual_engine,
                                                                  self.music_engine, self.level_engine, 1)

    def update(self) -> None:
        """ Do nothing. """
        pass

    def draw(self) -> None:
        """ Do nothing. """
        pass


class MusicEngine:
    """ Music engine: play/stop music, play sound, etc."""

    def __init__(self) -> None:
        self._base = Path("data/assets/musics/")

    def play_music(self, music_path: str | Path) -> None:
        """ Play the given music from music folder. """
        music_path = str(self._base / music_path)
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1)
        print(f":loud_sound: Play '{music_path}'")

    def play_sound(self):
        pass


@dataclass(frozen=True)
class Level:
    """ Level information. """
    name: str
    music: str
    background_color: list[int]
    background_img: str
    scenery_img: str


class LevelEngine:
    """ Level engine: load/start level. """

    def __init__(self) -> None:
        self._base = Path("data/level")

    def load(self, level: str) -> Level:
        """ Load the given level. """
        data = json.loads((self._base / f"{level}.json").read_text())
        schema = json.loads((self._base / "level.schema.json").read_text())
        validate(data, schema)
        return from_dict(data_class=Level, data=data, config=Config(strict=True, strict_unions_match=True))


class VisualEngine:
    """ Manage the VFX. """

    def __init__(self, screen: Surface | SurfaceType) -> None:
        self.FONT_SM = pygame.font.Font("data/assets/fonts/minya_nouvelle_bd.ttf", 32)
        self.FONT_MD = pygame.font.Font("data/assets/fonts/minya_nouvelle_bd.ttf", 64)
        self.FONT_LG = pygame.font.Font("data/assets/fonts/thats_super.ttf", 72)

        self.screen = screen
        self.background_layer = pygame.Surface([WIDTH, HEIGHT], pygame.SRCALPHA, 32)
        self.scenery_layer = pygame.Surface([WIDTH, HEIGHT], pygame.SRCALPHA, 32)

    def set_background(self, color: list[int], filepath: str) -> None:
        """ Set the background of the game. """
        filepath = f"data/assets/backgrounds/{filepath}"
        self.background_layer.fill(color)

        background_img = pygame.image.load(filepath).convert_alpha()
        h = background_img.get_height()
        w = int(background_img.get_width() * HEIGHT / h)
        background_img = pygame.transform.scale(background_img, (w, HEIGHT))
        for x in range(0, WIDTH, background_img.get_width()):
            self.background_layer.blit(background_img, [x, 0])

        self.screen.blit(self.background_layer, (0, 0))
        pygame.display.flip()

    def set_scenery(self, filepath: str) -> None:
        """ Set the scenery in front of the background. """
        filepath = f"data/assets/backgrounds/{filepath}"
        scenery_img = pygame.image.load(filepath).convert_alpha()
        h = scenery_img.get_height()
        w = int(scenery_img.get_width() * HEIGHT / h)
        scenery_img = pygame.transform.scale(scenery_img, (w, HEIGHT))
        for x in range(0, WIDTH, scenery_img.get_width()):
            self.scenery_layer.blit(scenery_img, [x, HEIGHT - scenery_img.get_height()])

        self.screen.blit(self.scenery_layer, (0, 0))
        pygame.display.flip()

    def write_centered_text(self, text: str, font: Font, color: tuple[int, int, int],
                            coord: tuple[int, int]) -> SurfaceType:
        """ Write some text on the screen. """
        render = font.render(text, True, color)
        self.screen.blit(render, (coord[0] - render.get_width() / 2, coord[1]))
        pygame.display.flip()
        return render


class GameEngine:
    """ Game loop. """

    def __init__(self) -> None:
        """ Initialize game engine. """
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.FULLSCREEN | pygame.SCALED, depth=32,
                                              vsync=1)
        pygame.display.set_caption(GAME_NAME)

        self.music_engine = MusicEngine()
        self.level_engine = LevelEngine()
        self.visual_engine = VisualEngine(self.screen)

        self.done = False
        self.current_state = SplashScreenState(self, self.visual_engine, self.music_engine, self.level_engine)

    def loop(self):
        """ Game loop. """
        while not self.done:
            self.current_state.process_events()
            self.current_state.update()
            self.current_state.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    traceback.install(width=120, show_locals=True)
    try:
        pygame.mixer.pre_init()
        pygame.init()

        GameEngine().loop()

        pygame.quit()
    except KeyboardInterrupt:
        print(f"[bold]Stopped by user.")
        sys.exit(EX_OK)
