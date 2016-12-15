#!/usr/bin/python3
# -*- coding: utf-8 -*-

import click
from pprint import pprint
import time
import random
import copy
import math

def load_instances(instances_file, solutions_file):
    instances = {}
    #~ ins = open(instances_file, 'r')
    with open(instances_file, 'r') as ins:
        for line in ins:
            data = line.split(' ')
            ins_size = int(data[1])
            instances[int(data[0])] = {
                'size': ins_size,
                'capacity': int(data[2]),
                'weights': list(map(int, data[3::2])),
                'prices': list(map(int, data[4::2])),
            }

    with open(solutions_file, 'r') as sol:
        for line in sol:
            data = line.split(' ')
            ins_id = int(data[0])
            instances[ins_id]['opt_sol'] = {
                'price': int(data[2]),
                'items': list(map(bool, map(int, data[4:]))),
            }
    return instances


def make_individual(size, p):
    # return { 'dna': [ random.random() < p for i in range(size) ] }
    return { 'dna': [ random.random() < 0.5 for i in range(size) ] }


def repair_individual(instance, individual):
    indexes = [i for i in range(instance['size'])]
    # print(indexes)
    random.shuffle(indexes)
    # print(indexes)
    # for i in instance['rep_ord']:
    for i in indexes:
        # print(i)
        if individual['weight'] < instance['capacity']:
            return
        if individual['dna'][i] == True:
            individual['dna'][i] = False
            individual['price'] -= instance['prices'][i]
            individual['weight'] -= instance['weights'][i]


def fill_properties(instance, individual):
    price = 0
    weight = 0
    for i in range(instance['size']):
        if individual['dna'][i] == True:
            price += instance['prices'][i]
            weight += instance['weights'][i]
    individual['price'] = price
    individual['weight'] = weight


def init_population(instance, pop_size):
    capacity = instance['capacity']
    size = instance['size']
    # tot_weight = sum(instance['weights'])
    # p = capacity / tot_weight
    # instance['p'] = p
    p = instance['p']
    population = []
    for i in range(pop_size):
        individual = make_individual(size, p)
        fill_properties(instance, individual)
        repair_individual(instance, individual)
        population.append(individual)
    population.sort(key=lambda x: x['price'], reverse=True)
    return population


def crossover(instance, population, pop_size, cross_f):
    child_cnt = int(pop_size*cross_f)
    size = instance['size']
    for i in range(child_cnt):
        a = random.randint(0, pop_size-1)
        b = random.randint(0, pop_size-1)
        while a==b:
            b = random.randint(0, pop_size-1)
        d = random.randint(0, size)
        individual = { 'dna': [ population[a]['dna'][i] if (i < d) else population[b]['dna'][i] for i in range(size) ] }
        fill_properties(instance, individual)
        # repair_individual(instance, individual)
        population.append(individual)
    return population


def mutation(instance, population, mut_f, mut_s):
    pop_size = len(population)
    mutants_cnt = math.ceil(pop_size*mut_f)
    # print(mutants_cnt)
    size = instance['size']
    for i in range(mutants_cnt):
        a = random.randint(0, pop_size-1)
        for j in range(math.ceil(mut_s*size)):
            k = random.randint(0, size-1)
            population[a]['dna'][k] = not population[a]['dna'][k]
        fill_properties(instance, population[a])
    return population


def evolution(instance, ins_id, pop_size, gen_cnt):
    data = [(i, instance['prices'][i]) for i in range(instance['size'])]
    data.sort(key=lambda item: item[1])
    instance['rep_ord'] = list(map((lambda item: item[0]), data))
    instance['p'] = instance['capacity'] / sum(instance['weights'])
    population = init_population(instance, pop_size)
    # for ind in population:
    #     print(ind)
    cross_f = 0.80
    elite_cnt = 1
    best_price = 0
    dna_degradation = 0
    for g in range(gen_cnt):
        elites = []
        for i in range(elite_cnt):
            elites.append(copy.deepcopy(population[i]))
        mutation(instance, population, 0.1+dna_degradation, 0.1+0.33*dna_degradation)
        population = crossover(instance, population, pop_size, cross_f)
        for ind in population:
            repair_individual(instance, ind)
        for ind in elites:
            population.append(ind)
        population.sort(key=lambda x: x['price'], reverse=True)
        population = population[:pop_size]
        # for ind in population:
        #     print(ind)
        if best_price == population[0]['price'] and dna_degradation<0.5 :
            dna_degradation += 0.02
        else:
            dna_degradation = 0
            best_price = population[0]['price']
        print('{};{};{}'.format(population[0]['price'],population[-1]['price'],population[pop_size//2]['price']))
    instance['evo_sol'] = {}
    instance['evo_sol']['price'] = population[0]['price']
    instance['evo_sol']['weight'] = population[0]['weight']
    instance['evo_sol']['items'] = population[0]['dna']


def print_sol(instance, sol_to_print, id_sol, time=None):
    sol = instance[sol_to_print]
    opt_price = instance['opt_sol']['price']

    print('{};{};{};{};'.format(id_sol, len(sol['items']), sol['price'], sol['weight'], sol['price']/opt_price),end='')
    print('{};{:.04f};'.format(opt_price, sol['price']/opt_price), end='')
    if time:
        print('{:.04f};'.format(time),end='')
    #~ if instace_info:
    tot_price = sum(instance['prices'])
    max_price = max(instance['prices'])
    tot_weight = sum(instance['weights'])
    print('{};{};{};{};'.format(instance['capacity'],tot_weight,tot_price,max_price),end='')
    for item in sol['items']:
        print('{};'.format(item),end='')
    print()

@click.command()
@click.option(
    '--instances-file', '-i',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True),
    help='path to file with instances', prompt='Enter path to file with instances'
)
@click.option(
    '--solutions-file', '-s',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, writable=False, readable=True, resolve_path=True),
    help='path to file with solutions', prompt='Enter path to file with solutions'
)
@click.option(
    '--repeats', '-r', default=1, type=click.IntRange(1, 1000),
    help='number of retition of each instance'
)
@click.option(
    '--population', '-p', default=100, type=click.IntRange(1, 1000000),
    help='size of population'
)
@click.option(
    '--generations', '-g', default=100, type=click.IntRange(1, 1000000),
    help='number of generations'
)
@click.option('--time-measure', '-t', default=True, type=click.BOOL, help='display time per insance')
def main(instances_file, solutions_file, time_measure, repeats, population, generations):
    instances = load_instances(instances_file, solutions_file)
    index = 1
    sol_to_print = 'evo_sol'
    for key, instance in instances.items():
        if time_measure:
            start = time.time()
        for i in range(repeats):
            evolution(instance, key, population, generations)
        if time:
            print_sol(instance, sol_to_print, key, (time.time() - start)/repeats)
        else:
            print_sol(instance, sol_to_print, key)
        index += 1
        if index > 1:
            exit(0)
    return 0


if __name__ == '__main__':
    main()
