import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import pickle

from makeGraph import *

INF_val = 999999 # infinite
m = 0.02 # the ratio to compare construction cost and saved cost
hubBasicCost = 500000
hubPerOrderCost = 0.1

class orderSolution_struct(object):
    path = []
    edge = []
    order = Order()
    arrivalTime = []
    cost = 0

    def currentIndex(self, cityIndex):
        return self.path.index(cityIndex)


# read in graph from pkl file
pkl_file = open('graph.pkl', 'rb')
graph = pickle.load(pkl_file)
print('Read in graph Done!')
pkl_file.close()

# # read in sheet for orders and commodities
# pkl_orders = open('sheet_orders.pkl', 'rb')
# pkl_commodities = open('sheet_commodities.pkl', 'rb')
# sheet_orders = pickle.load(pkl_orders)
# sheet_commodities = pickle.load(pkl_commodities)
# print('Read in sheets for tables Done!')
# pkl_orders.close()
# pkl_commodities.close()

# construction of order
def getOrder(i):
    order = Order()
    order.index = i-1
    order.start = sheet_orders.cell(row=i, column=1).value
    order.end = sheet_orders.cell(row=i, column=2).value
    orderTime = sheet_orders.cell(row=i, column=3).value
    order.orderTime = orderTime.hour * 3600 + orderTime.minute * 60 + orderTime.second  # compare with seconds
    order.goods = sheet_orders.cell(row=i, column=4).value
    order.amount = sheet_orders.cell(row=i, column=5).value
    order.isEmergency = sheet_orders.cell(row=i, column=6).value
    order.totalWeight = sheet_commodities.cell(row=order.goods + 1, column=4).value * order.amount
    return order

def seconds2time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    time = "%02d:%02d:%02d" % (h, m, s)
    return time

# run optimalPathSearch and get orderSolutions
def getOrderSolutions(orderNum):

    orderSolutions = []

    orderIndexNum = 2
    while (sheet_orders.cell(row=orderIndexNum, column=1).value):

        # if orderIndexNum > orderNum:
        #     break

        order = getOrder(orderIndexNum)

        # initial for dijkstra
        select_node_list = []
        node_dic = {}
        select_node_list.append(order.start)
        for index in range(len(graph)):
            node_dic[index + 1] = [INF_val, -1, -1, 0]  # current cost, preorder edge, arrival time, passedTime
        node_dic[order.start] = [0, -1, order.orderTime, 0]  # set the start node
        for edge in graph[order.start - 1].edges:
            weight = edge.weight(order, order.orderTime)
            transTime = edge.distance / edge.speed * 3600 + edge.delayTime * 60
            waitTime = (edge.departureTime - order.orderTime if (
                        order.orderTime <= edge.departureTime) else DAY_SEC - order.orderTime + edge.departureTime)  # the time to wait for departure
            arrivalTime = (order.orderTime + waitTime + transTime) % DAY_SEC
            oldNode_dic = node_dic[edge.end]

            node_dic[edge.end][0] = weight
            node_dic[edge.end][1] = edge
            node_dic[edge.end][2] = arrivalTime
            node_dic[edge.end][3] = waitTime + transTime

        # execution of dijkstra
        while (len(select_node_list) < CITY_NUM):
            min_key = -1
            min_val = INF_val
            # find the current nearest node
            for key, val in node_dic.items():
                if key not in select_node_list and val[0] < min_val:
                    min_key = key
                    min_val = val[0]

            # insert into selected list
            if min_key != -1:
                select_node_list.append(min_key)
                min_dic = node_dic[min_key]
            else:
                break

            # update the dictionary
            for edge in graph[min_key - 1].edges:
                oldNode_dic = node_dic[edge.end]
                weight = edge.weight(order, min_dic[2])
                if oldNode_dic[0] > weight + min_dic[0]:
                    transTime = edge.distance / edge.speed * 3600 + edge.delayTime * 60
                    waitTime = (edge.departureTime - min_dic[2] if (min_dic[2] <= edge.departureTime) else DAY_SEC - min_dic[2] + edge.departureTime)  # the time to wait for departure
                    arrivalTime = (min_dic[2] + waitTime + transTime) % DAY_SEC

                    node_dic[edge.end][0] = weight + min_dic[0]
                    node_dic[edge.end][1] = edge
                    node_dic[edge.end][2] = arrivalTime
                    node_dic[edge.end][3] = min_dic[3] + transTime + waitTime

        # format the path(include the start node but not include the end node)
        path = []
        preorderNode = node_dic[order.end][1].start
        while preorderNode != order.start:
            path.append(preorderNode)
            preorderNode = node_dic[preorderNode][1].start
        path.append(order.start)
        path.reverse()

        # format orderSolution
        orderSolution = orderSolution_struct()
        orderSolution.order = order # solution.order
        orderSolution.path = path # solution.path
        orderSolution.cost = node_dic[order.end][0] # solution.cost

        orderSolution.edge = []
        for i in range(1, len(path)): # solution.edge
            orderSolution.edge.append(node_dic[path[i]][1])
        orderSolution.edge.append((node_dic[order.end][1]))

        orderSolution.arrivalTime = []
        orderSolution.arrivalTime.append(order.orderTime) # solution.arrivalTime
        for i in range(1, len(path)):
            orderSolution.arrivalTime.append((node_dic[path[i]][2]))

        print('order %d solution:' % order.index)
        print('path:', orderSolution.path)
        print('edge:')
        for edge in orderSolution.edge:
            print('(%d, %d)' % (edge.start, edge.end), 'take %s' % edge.way, 'departureTime: %s' % seconds2time(edge.departureTime))
        print('arrivalTime:', list(map(seconds2time, orderSolution.arrivalTime)))
        print('cost:', orderSolution.cost)
        print('')

        orderSolutions.append(orderSolution)

        orderIndexNum += 1

    output = open('orderSolutions_all.pkl', 'wb')
    pickle.dump(orderSolutions, output)
    print('Write out orderSolutions Done!')
    output.close()
    exit()


if __name__ == '__main__':

    # get orderSolutions OR read in orderSolutions

    # getOrderSolutions(200000)

    pkl_orderSolutions = open('orderSolutions.pkl', 'rb')
    orderSolutions = pickle.load(pkl_orderSolutions)
    print('Read in orderSolutions Done!')
    pkl_orderSolutions.close()

    hubs = []
    # check each city that whether it can be constructed as a hub
    for city in graph:
        # find relative orderSolutions
        relativeOrderSolutions = [] # the solutions that use current city as start or transfer
        for solution in orderSolutions:
            if city.index in solution.path:
                relativeOrderSolutions.append(solution)


        # confirm the only transport tool for each relative city from the current city
        transportTool = {} # store the edges we choose from the current city to relative city
        for solution in relativeOrderSolutions:
            currentIndex = solution.path.index(city.index)
            if (solution.edge[currentIndex].end in transportTool):
                transportTool[solution.edge[currentIndex].end][0] += 1
                transportTool[solution.edge[currentIndex].end][1].append(solution)
            else:
                transportTool[solution.edge[currentIndex].end] = [1, [solution], -1] # the number of orders using this way, the corresponding orderSolutions, the edge we decide to use
        for postCity, postCityAttr in transportTool.items():
            # if the relative city is only used once, we use the edge it used before
            if postCityAttr[0] == 1:
                currentIndex = postCityAttr[1][0].path.index(city.index)
                postCityAttr[2] = postCityAttr[1][0].edge[currentIndex]

            # if the relative city is used by multiple order, then we compute each to find a best one
            else:
                minCost = INF_val
                bestSolution = orderSolution_struct()
                for solutionChosen in postCityAttr[1]:
                    totalCost = 0
                    currentIndex = solutionChosen.path.index(city.index)
                    edgeChosen = solutionChosen.edge[currentIndex]
                    for eachSolution in postCityAttr[1]:
                        totalCost += edgeChosen.hub_weight(eachSolution.order,
                                                       eachSolution.arrivalTime[eachSolution.currentIndex(city.index)])
                    if totalCost < minCost:
                        minCost = totalCost
                        bestSolution = solutionChosen
                postCityAttr[2] = bestSolution.edge[bestSolution.currentIndex(city.index)]
        # Now the dictionary 's third value store the edge we should choose


        # Now assume that we construct a hub at the current city, we compute the cost it save
        noHubCost = 0
        hubCost = 0
        for solution in relativeOrderSolutions:
            noHubCost += solution.cost
            hubCostPerSolution = 0
            for i in range(len(solution.path)):
                if solution.edge[i].start != city.index:
                    hubCostPerSolution += solution.edge[i].weight(solution.order, solution.arrivalTime[i])
                    #update the following arrivalTime
                    if i != (len(solution.path) - 1):
                        solution.arrivalTime[i+1] = solution.arrivalTime[i] + solution.edge[i].waitTimeAndTransTime(solution.arrivalTime[i])
                    print('(%d, %d)' % (solution.edge[i].start, solution.edge[i].end), 'departureTime:', seconds2time(solution.edge[i].departureTime))
                else: # start from the current city (assumming to be hub) and we need to modify the following arrivalTime
                    edgeChosen = transportTool[solution.edge[i].end][2]
                    hubCostPerSolution += edgeChosen.hub_weight(solution.order, solution.arrivalTime[i])
                    #update the following arrivalTime
                    if i != (len(solution.path) - 1):
                        solution.arrivalTime[i+1] = solution.arrivalTime[i] + edgeChosen.waitTimeAndTransTime(solution.arrivalTime[i])
                    print('(%d, %d)' % (solution.edge[i].start, solution.edge[i].end), 'departureTime:', seconds2time(solution.edge[i].departureTime))


            hubCost += hubCostPerSolution

        savedCost = noHubCost - hubCost
        if savedCost > m*(hubBasicCost + len(relativeOrderSolutions)*hubPerOrderCost) / MONEYCOST_RATIO:
            hubs.append(city.index)



        print('current city', city.index)
        print('noHubCost', noHubCost)
        print('hubCost', hubCost)
        print('')

    print('The list that we choose to construct hubs is:', hubs)








