import collections
import math
import random
import maya.cmds as cmds
from maya.OpenMaya import MVector

from core import scene_util

frame_step_size = 5
epoch_count = 10
mutation_rate = 0.1
mutation_chance = 0.5
population_count = 10
champion_count = 5
foreign_count = 5

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])

morph_targets = ['Brow_Raise_Inner_L',
                 'Brow_Raise_Inner_R',
                 'Brow_Raise_Outer_L',
                 'Brow_Raise_Outer_R',
                 'Brow_Drop_L',
                 'Brow_Drop_R',
                 'Brow_Raise_L',
                 'Brow_Raise_R',
                 'Nose_Scrunch',
                 'Nose_Flank_Raise_L',
                 'Nose_Flank_Raise_R',
                 'Cheek_Raise_L',
                 'Cheek_Raise_R',
                 'Mouth_Smile_L',
                 'Mouth_Smile_R',
                 'Mouth_Frown_L',
                 'Mouth_Frown_R',
                 'Mouth_Dimple_L',
                 'Mouth_Dimple_R',
                 'Eye_Squint_L',
                 'Eye_Squint_R']


def create_progress_window(size):
    win = cmds.window(title='Genetic Matching', toolbox=True)
    cmds.columnLayout()
    progress = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress.window)
    return progress


def get_morpher_name():
    return 'Morpher_CC_Base_Body'


def get_morph_targets():
    result = []
    for morph in morph_targets:
        result.append(get_morpher_name() + '.' + morph)
    return result


class Organism:
    fitness = 9999999.

    def __init__(self, parents=None):
        self.genes = []
        for morph_index in get_morph_targets():
            self.genes.append(random.random())
        if parents is not None:
            for gene_index in range(len(self.genes)):
                self.genes[gene_index] = parents[0].genes[gene_index] if random.random() > 0.5 else parents[1].genes[gene_index]
                if random.random() > mutation_chance:
                    mutation_sign = 1 if random.random() > 0.5 else -1
                    self.genes[gene_index] = math.tanh(self.genes[gene_index] + (mutation_rate * mutation_sign))
                    self.genes[gene_index] = max(self.genes[gene_index], 0.0)

    def set_fitness(self, fit):
        self.fitness = fit

    def __lt__(self, other):
        return self.fitness < other.fitness


def get_object_world_position(item):
    translation = cmds.xform(item, query=True, worldSpace=True, translation=True)
    result = MVector(translation[0], translation[1], translation[2])
    return result


def get_sum_error(source_vectors, target_list):
    sum_distance = 0  # TODO: include error from previous frame
    for source, target in zip(source_vectors, target_list):
        target_point = get_object_world_position(target)
        sum_distance += (source - target_point).length()
    return sum_distance


def set_scene_to_organism(o, key=False):
    cmds.select(get_morpher_name())
    for gene, attribute in zip(o.genes, get_morph_targets()):
        cmds.setAttr(attribute, gene)
        if key:
            cmds.setKeyframe(attribute)


def build_organism_from_scene():
    result = Organism()
    for index, attribute in enumerate(get_morph_targets()):
        result.genes[index] = cmds.getAttr(attribute)
    return result


cmds.select('capture_points', replace=True)
capture_points = cmds.ls(selection=True)
capture_points.sort()
cmds.select('target_points', replace=True)
target_points = cmds.ls(selection=True)
target_points.sort()

time_range = scene_util.get_timeline_selection()
progress_window = create_progress_window(epoch_count * ((int(time_range[1]) - int(time_range[0])) / frame_step_size) * population_count)


for time in range(int(time_range[0]), int(time_range[1])):
    if time % frame_step_size == 0:
        cmds.currentTime(time)

        capture_vectors = []
        for c in capture_points:
            capture_vectors.append(get_object_world_position(c))

        most_fit = build_organism_from_scene()
        set_scene_to_organism(most_fit)
        most_fit.set_fitness(get_sum_error(capture_vectors, target_points))

        population = []
        for i in range(population_count):
            new_organism = Organism()
            organism = Organism([most_fit, new_organism])
            population.append(organism)

        for epoch in range(epoch_count):
            for organism in population:
                set_scene_to_organism(organism)
                organism.set_fitness(get_sum_error(capture_vectors, target_points))
                cmds.progressBar(progress_window.control, edit=True, step=1)
                if organism.fitness < most_fit.fitness:
                    most_fit = organism
                    set_scene_to_organism(most_fit)

            '''
            population.sort()
            new_population = []
            for new_index in range(population_count):
                if new_index < foreign_count:
                    new_population.append(Organism([most_fit, Organism()]))
                else:
                    new_population.append(Organism([most_fit, population[random.randrange(1, champion_count)]]))
            population = new_population
            '''

            population.sort()
            new_population = []
            for new_index in range(population_count):
                new_population.append(Organism([most_fit, population[random.randrange(1, champion_count)]]))
            population = new_population

        set_scene_to_organism(most_fit, True)  # may not be necessary because of auto key
        cmds.setKeyframe(get_morpher_name(), t=[time], at='error', v=most_fit.fitness)

cmds.deleteUI(progress_window.window)
