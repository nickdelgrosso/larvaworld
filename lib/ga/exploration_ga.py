import sys
import pygame


from pygame.locals import *

from lib.conf.base.dtypes import null_dict
from lib.ga.exploration.ga_engine import GaLarvaEngine
from lib.ga.robot.larvaConfDic import LarvaConfDic
from lib.ga.robot.larva_robot import LarvaRobot
from lib.ga.scene.scene import Scene
from lib.ga.util.color import Color
from lib.ga.util.scene_type import SceneType
from lib.ga.util.side_panel import SidePanel
from lib.ga.util.time_util import TimeUtil


class ExplorationGA:

    DEFAULT_SCENE_FILE = 'saved_scenes/no_boxes.txt'
    DEFAULT_SCENE_SPEED = 0  # 0 = maximum frame rate
    DEFAULT_VERBOSE_VALUE = 0  # 0, 1, 2
    SCENE_MAX_SPEED = 3000
    SIDE_PANEL_WIDTH = 480

    def __init__(self,**kwargs):
        self.scene = None
        self.screen = None
        self.engine = None
        self.side_panel = None
        self.population_num = None
        self.scene_speed = None
        self.scene_file = None
        self.elitism_num = None
        self.robot_random_direction = None
        self.multicore = None
        self.obstacle_sensor_error = None
        self.mutation_probability = None
        self.mutation_coefficient = None
        self.selection_ratio = None
        self.verbose = None
        self.long_lasting_generations = None

        self.parse_cli_arguments()
        pygame.init()
        pygame.display.set_caption("Free Exploration Evolution")
        clock = pygame.time.Clock()
        self.initialize(**kwargs)


        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    sys.exit()
                elif event.type == KEYDOWN and event.key == K_r:
                    self.initialize()
                elif event.type == KEYDOWN and (event.key == K_PLUS or event.key == 93 or event.key == 270):
                    self.increase_scene_speed()
                elif event.type == KEYDOWN and (event.key == K_MINUS or event.key == 47 or event.key == 269):
                    self.decrease_scene_speed()
                elif event.type == KEYDOWN and event.key == K_s:
                    self.engine.save_genomes()

            start_time = TimeUtil.current_time_millis()
            self.engine.step()
            end_time = TimeUtil.current_time_millis()
            step_duration = end_time - start_time
            self.printd(2, 'Step duration: ', step_duration)

            self.screen.fill(Color.BLACK)

            for obj in self.scene.objects:
                obj.draw(self.screen)

                if issubclass(type(obj), LarvaRobot) and obj.unique_id is not None:
                    obj.draw_label(self.screen)

            # draw a black background for the side panel
            side_panel_bg_rect = pygame.Rect(self.scene.width, 0, self.SIDE_PANEL_WIDTH, self.scene.height)
            pygame.draw.rect(self.screen, Color.BLACK, side_panel_bg_rect)

            self.side_panel.display_ga_info_larva(LarvaConfDic)

            pygame.display.flip()
            int_scene_speed = int(round(self.scene.speed))
            clock.tick(int_scene_speed)

    def initialize(self,**kwargs):

        self.scene = Scene.load_from_file(self.scene_file, self.scene_speed, self.SIDE_PANEL_WIDTH)
        self.screen = self.scene.screen
        self.side_panel = SidePanel(self.scene, self.population_num)
        self.engine = GaLarvaEngine(self.scene, self.side_panel, self.population_num, self.elitism_num,
                               self.robot_random_direction, self.multicore, self.obstacle_sensor_error,
                               self.mutation_probability, self.mutation_coefficient, self.selection_ratio,
                               self.long_lasting_generations, self.verbose,**kwargs)

    def increase_scene_speed(self):
        if self.scene.speed < self.SCENE_MAX_SPEED:
            self.scene.speed *= 1.5

        print('Scene speed:', self.scene.speed)

    def decrease_scene_speed(self):
        if self.scene.speed == 0:
            self.scene.speed = self.SCENE_MAX_SPEED

        if self.scene.speed > 1:
            self.scene.speed /= 1.5

        print('Scene speed:', self.scene.speed)

    def parse_cli_arguments(self):
        from lib.ga.util.cli_parser import CliParser
        parser = CliParser()
        parser.parse_args(self.DEFAULT_SCENE_FILE, self.DEFAULT_SCENE_SPEED, SceneType.GA_OBSTACLE_AVOIDANCE)

        self.elitism_num = parser.elitism_num
        self.population_num = parser.population_num
        self.mutation_probability = parser.mutation_probability
        self.mutation_coefficient = parser.mutation_coefficient
        self.robot_random_direction = parser.robot_random_direction
        self.scene_speed = parser.scene_speed
        self.scene_file = parser.scene_file
        self.obstacle_sensor_error = parser.obstacle_sensor_error
        self.selection_ratio = parser.selection_ratio
        self.multicore = parser.multicore
        self.verbose = parser.verbose
        self.long_lasting_generations = parser.long_lasting_generations
        # print(self.multicore)
        # raise

    def printd(self, min_debug_level, *args):
        if self.verbose >= min_debug_level:
            msg = ''

            for arg in args:
                msg += str(arg) + ' '

            print(msg)


if __name__ == '__main__':
    ExplorationGA(dt=1/16, arena=null_dict('arena', arena_dims=(0.5, 0.5), arena_shape='rectangular'))
