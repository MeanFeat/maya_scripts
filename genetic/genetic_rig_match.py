import maya.cmds as cmds
from pymel.core import *
import random
import core.scene_util as scene_utils

sel = cmds.ls(selection=True)
cmds.select(sel[0], hierarchy=True)
target_skeleton = cmds.ls(selection=True)
cmds.select(cmds.editDisplayLayerMembers("*:ExportJoint", query=True), hierarchy=True)
match_skeleton = cmds.ls(selection=True, type='joint')
controls = cmds.editDisplayLayerMembers("*:Controls", query=True)

target_skeleton.sort()
match_skeleton.sort()


def get_attributes():
    return ["rotateX", "rotateY", "rotateZ"]


def get_joint_squared_error(a, b):
    result = 0.0
    #for attr in get_attributes():
    #    diff = cmds.getAttr(a + '.' + attr) - cmds.getAttr(b + '.' + attr)
    #    result += diff * diff
    a_vector = cmds.xform(a, ro=True, q=True)
    b_vector = cmds.xform(b, ro=True, q=True)
    for index, coord in enumerate(a_vector):
        diff = coord - b_vector[index]
        result += diff * diff

    a_vector = cmds.xform(a, t=True, ws=True, q=True)
    b_vector = cmds.xform(b, t=True, ws=True, q=True)
    for index, coord in enumerate(a_vector):
        diff = coord - b_vector[index]
        result += diff * diff

    return result


class MatchOrganism:
    cost = 0.0
    rotations = []

    def __init__(self):
        self.cost = 0.0
        self.rotations = []

    def apply_organism(self):
        index = 0
        for ctrl in controls:
            for attr in get_attributes():
                if not cmds.getAttr(ctrl + '.' + attr, lock=True):
                    cmds.setAttr(ctrl + '.' + attr, self.rotations[index])
                index += 1

    def update_cost(self):
        self.cost = 0.0
        self.apply_organism()
        for i in range(0, len(target_skeleton)-1):
            self.cost += get_joint_squared_error(target_skeleton[i], match_skeleton[i])


class Population:
    def __init__(self, count, mutation_chance, mutation_amount, champion_count):
        self.maxCount = count
        self.mutationChance = mutation_chance
        self.mutAmount = mutation_amount
        self.champCount = champion_count
        self.organisms = []
        for id in range(0, count):
            organism = MatchOrganism()
            for ctrl in controls:
                for attr in get_attributes():
                    current_rotation = cmds.getAttr(ctrl + '.' + attr)
                    mutation = -mutation_amount + (random.random() * mutation_amount * 2) if random.random() < self.mutationChance else 0.0
                    organism.rotations.append(current_rotation + mutation)
            self.organisms.append(organism)

    def Sort(self):
        self.organisms = sorted(self.organisms, key=lambda x: getattr(x, 'cost'), reverse=False)

    def BreedChild(self, p1, p2):
        child = MatchOrganism()
        for k in range(len(p1.rotations)):
            bred_rot = p1.rotations[k] if random.randint(0, 1) else p2.rotations[k]
            if random.random() < self.mutationChance:
                bred_rot += -self.mutAmount + (random.random() * self.mutAmount * 2)
            child.rotations.append(bred_rot)
        return child


def NextGen(pop):
    for organism_index in range(pop.champCount, pop.maxCount):
        pop.organisms[organism_index] = pop.BreedChild(pop.organisms[random.randint(0, pop.champCount)], pop.organisms[random.randint(0, pop.champCount)])
        for rotation_index, rotation in enumerate(pop.organisms[organism_index].rotations):
            if random.random() < pop.mutationChance:
                pop.organisms[organism_index].rotations[rotation_index] += -pop.mutAmount + (random.random() * pop.mutAmount * 2)
    for o in pop.organisms:
        o.update_cost()
    pop.Sort()

    pop.organisms[0].apply_organism()
    cmds.refresh()
    return pop




# while pop.organisms[0].cost > 0.25:
# NextGen()
# pop.mutAmount = 1 * pop.organisms[0].cost if pop.organisms[0].cost < 3 else 1
