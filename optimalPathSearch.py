import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import pickle
import pprint

from makeGraph import *

INF_val = 999999 # infinite
runOrderNumber = 100

# read in graph from pkl file
pkl_file = open('graph.pkl', 'rb')
graph = pickle.load(pkl_file)
print('Read in graph Done!')
pkl_file.close()

# read in sheet for orders and commodities
pkl_orders = open('sheet_orders.pkl', 'rb')
pkl_commodities = open('sheet_commodities.pkl', 'rb')
sheet_orders = pickle.load(pkl_orders)
sheet_commodities = pickle.load(pkl_commodities)
print('Read in sheets for tables Done!')
pkl_orders.close()
pkl_commodities.close()

hubChoose = []



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

if __name__ == '__main__':
    orderIndexNum = 2
    while (sheet_orders.cell(row=orderIndexNum, column=1).value):

        if orderIndexNum > runOrderNumber:
            break

        order = getOrder(orderIndexNum)

        # initial for dijkstra
        select_node_list = []
        node_dic = {}
        select_node_list.append(order.start)
        for index in range(len(graph)):
            node_dic[index+1] = [INF_val, -1, -1, 0] # current cost, preorder edge, arrival time, passedTime
        node_dic[order.start] = [0, -1, order.orderTime, 0] # set the start node
        for edge in graph[order.start-1].edges:
            weight = edge.weight(order, order.orderTime)
            transTime = edge.distance / edge.speed * 3600 + edge.delayTime * 60
            waitTime = (edge.departureTime - order.orderTime if (order.orderTime <= edge.departureTime) else DAY_SEC - order.orderTime + edge.departureTime)  # the time to wait for departure
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
            for edge in graph[min_key-1].edges:
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


        # format the path (not include the start node)
        path = []
        path.append(order.end)
        preorderNode = node_dic[order.end][1].start
        while preorderNode != order.start:
            path.append(preorderNode)
            preorderNode = node_dic[preorderNode][1].start
        path.reverse()

        # print the path and compute the total time and cost
        totalCost = 0
        print('The transport solution we choose for order (%d) is as follows: (totalWeight: %f)' % (order.index, order.totalWeight))
        for i in range(len(path)):
            edge = node_dic[path[i]][1]
            edgeCost = order.totalWeight * edge.unitCost * (edge.distance/50)
            totalCost += edgeCost
            start = edge.start
            end = edge.end
            way = edge.way
            departureTime = seconds2time(edge.departureTime)
            arrivalTime = seconds2time(node_dic[path[i]][2])
            print('Deliver from city %d to city %d, taking %s, departure at %s, arrive at %s, distance: %f, speed: %f, unitCost: %f, cost: %f' % (start, end, way, departureTime, arrivalTime, edge.distance, edge.speed, edge.unitCost, edgeCost))

        startTime = order.orderTime
        endTime = node_dic[path[i]][2]
        totalTime = node_dic[path[i]][3]
        m, s = divmod(totalTime, 60)
        h, m = divmod(m, 60)


        print('The total cost for delivery is', totalCost)
        print('orderTime:', seconds2time(startTime), 'endTime:', seconds2time(endTime), 'totalTime: %d hours, %d minutes, %d seconds' % (h, m, s), 'whick is %d seconds' % totalTime)
        print('')
        print('')

        orderIndexNum += 1




