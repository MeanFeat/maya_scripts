import collections
import math
import random
import maya.cmds as cmds
from maya.OpenMaya import MProfilingScope, MProfiler
from maya.api.OpenMaya import MVector, MTime
from maya.api import OpenMaya
from maya.api.MDGContextGuard import MDGContextGuard

from core import scene_util

frame_step_size = 3
epoch_count = 20
mutation_rate = 0.005
mutation_chance = 0.75
population_count = 20
champion_count = 5

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])
categoryIndex = MProfiler.addCategory("Facial Genetic")
morph_targets = None

morph_target_names = ['Brow_Raise_Inner_L',
                      'Brow_Raise_Inner_R',
                      'Brow_Raise_Outer_L',
                      'Brow_Raise_Outer_R',
                      'Brow_Drop_L',
                      'Brow_Drop_R',
                      'Brow_Raise_L',
                      'Brow_Raise_R',
                      'Nose_Scrunch']


def create_progress_window(size):
    win = cmds.window(title='Genetic Matching', toolbox=True)
    cmds.columnLayout()
    progress = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress.window)
    return progress


def get_morpher_name():
    return 'Morpher_CC_Base_Body'


def get_morph_targets():
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorB_L2, "get_morph_targets", "Facial Genetic")
    global morph_targets
    if morph_targets is None:
        result = []
        for morph in morph_target_names:
            result.append(get_morpher_name() + '.' + morph)
        morph_targets = result
        return result
    else:
        return morph_targets


class Organism:
    fitness = 9999999.
    morph_vectors = []

    def __init__(self, parents=None, zero=False):
        profiler = MProfilingScope(categoryIndex, MProfiler.kColorB_L1, "initialize organism", "Facial Genetic")
        self.genes = []
        for morph_index in get_morph_targets():
            value = 0 if zero else random.random()
            self.genes.append(value)
        if parents is not None:
            for gene_index in range(len(self.genes)):
                self.genes[gene_index] = parents[0].genes[gene_index] if random.random() > 0.5 else parents[1].genes[gene_index]
                if random.random() > mutation_chance:
                    mutation_sign = 1 if random.random() > 0.5 else -1
                    self.genes[gene_index] = self.genes[gene_index] + ((mutation_rate * mutation_sign) * random.random())
                    # self.genes[gene_index] = math.tanh(self.genes[gene_index] + ((mutation_rate * mutation_sign) * random.random()))
                    # self.genes[gene_index] = max(self.genes[gene_index], 0.0)

    def set_fitness(self, fit):
        self.fitness = fit

    def __lt__(self, other):
        return self.fitness < other.fitness


def get_object_world_position(item):
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorA_L3, "get_object_world_position", "Facial Genetic")
    translation = cmds.xform(item, query=True, worldSpace=True, translation=True)
    result = MVector(translation[0], translation[1], translation[2])
    return result


def get_sum_error(source_vectors, target_vectors, fittest=None, current=None):
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorA_L2, "get_sum_error", "Facial Genetic")
    sum_error = 0  # TODO: include error from previous frame
    for source, target in zip(source_vectors, target_vectors):
        delta = source - target
        sum_error += delta.x ** 2
        sum_error += delta.y ** 2
        sum_error += delta.z ** 2
    if fittest is not None and current is not None:
        for fit, cur in zip(fittest.genes, current.genes):
            sum_error += ((cur - fit) ** 2)
    return sum_error


def set_scene_to_organism(o, time=None, key=False):
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorA_L1, "set_scene_to_organism", "Facial Genetic")
    cmds.select(get_morpher_name())
    for gene, attribute in zip(o.genes, get_morph_targets()):
        cmds.setAttr(attribute, gene)
        if key:
            cmds.setKeyframe(attribute, time=time)


def build_organism_from_scene():
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorE_L3, "build_organism_from_scene", "Facial Genetic")
    result = Organism()
    for index, attribute in enumerate(get_morph_targets()):
        result.genes[index] = cmds.getAttr(attribute)
    return result


def get_morph_deltas(setup, morphs, genes):
    profiler = MProfilingScope(categoryIndex, MProfiler.kColorE_L2, "get_morph_deltas", "Facial Genetic")
    result = []
    for null in range(len(setup)):
        vec = MVector()
        result.append(vec)
    for gene_index, g in enumerate(genes):
        for morph_index, m in enumerate(morphs[gene_index]):
            result[morph_index] += m * g
    for setup_index, s in enumerate(setup):
        result[setup_index] += s
    return result


def do_it():
    most_fit = Organism()
    cmds.select('capture_points', replace=True)
    capture_points = cmds.ls(selection=True)
    capture_points.sort()
    cmds.select('target_points', replace=True)
    target_points = cmds.ls(selection=True)
    target_points.sort()

    setup_organism = Organism(zero=True)
    set_scene_to_organism(setup_organism)
    setup_vectors = []
    for point in target_points:
        setup_vectors.append(get_object_world_position(point))

    morph_deltas = []
    for morph_index, morph_target in enumerate(get_morph_targets()):
        morph_organism = Organism(zero=True)
        morph_organism.genes[morph_index] = 1
        set_scene_to_organism(morph_organism)
        deltas = []
        for point_index, point in enumerate(target_points):
            deltas.append(get_object_world_position(point) - setup_vectors[point_index])
        morph_deltas.append(deltas)

    time_range = scene_util.get_timeline_selection()
    frame_count = ((int(time_range[1]) - int(time_range[0])) / frame_step_size)
    progress_window = create_progress_window((epoch_count * frame_count * population_count))
    start = int(time_range[0])
    end = int(time_range[1])
    most_fit_cached = Organism()
    capture_vectors_list = []
    for time in range(start, end):
        if time % frame_step_size == 0:
            capture_vectors = []  # TODO: MDGContext guard and cache all frames outside of loop
            with MDGContextGuard(OpenMaya.MDGContext(MTime(time, MTime.uiUnit()))) as guard:
                for c in capture_points:
                    capture_vectors.append(get_object_world_position(c))
            capture_vectors_list.append(capture_vectors)

    for time in range(start, end):
        if time % frame_step_size == 0:
            capture_vectors = capture_vectors_list[int((time-start)/frame_step_size)]
            most_fit = build_organism_from_scene()  # TODO: cache and maintain
            target_vectors = get_morph_deltas(setup_vectors, morph_deltas, most_fit.genes)
            most_fit.set_fitness(get_sum_error(capture_vectors, target_vectors))

            population = []
            for population_index in range(population_count):
                new_organism = Organism()
                organism = Organism([most_fit, new_organism])
                population.append(organism)
            for epoch in range(epoch_count):
                for organism in population:
                    target_vectors = get_morph_deltas(setup_vectors, morph_deltas, organism.genes)
                    organism.set_fitness(get_sum_error(capture_vectors, target_vectors, most_fit_cached, organism))
                    cmds.progressBar(progress_window.control, edit=True, step=1)
                    if organism.fitness < most_fit.fitness:
                        most_fit = organism

                population.sort()
                new_population = []
                for new_index in range(population_count):  # TODO: catch duplicates
                    new_population.append(Organism([most_fit, population[random.randrange(1, champion_count)]]))
                population = new_population

            most_fit_cached = most_fit
            set_scene_to_organism(most_fit, time, True)
    cmds.deleteUI(progress_window.window)
