import json
from itertools import islice

from termcolor import cprint


available_isk = 400_000_000
minimum_profit = 250_000
sales_tax = 0.08 - (0.08*.11)*5
buy_tax = 0

analysis_path = 'data/analysis.json'
with open(analysis_path, 'r') as f:
    analysis = json.load(f)


def trade_until_oom_or_unprofitable(bpv, spv, available_isk):
    bpv = [list(x) for x in bpv.items()][::-1]
    spv = [list(x) for x in spv.items()][::-1]
    # print(bpv, spv)

    current_isk = available_isk
    total_profit = 0
    volume = 0
    while bpv:
        if len(spv) == 0:
            break

        lowest_sell = float(spv[-1][0])
        highest_buy = float(bpv[-1][0])
        if highest_buy*(1-sales_tax) > lowest_sell and current_isk > lowest_sell: # Still profit to be made
            total_profit += highest_buy*(1-sales_tax) - lowest_sell
            current_isk -= lowest_sell
            volume += 1

            spv[-1][1] -= 1
            bpv[-1][1] -= 1
            if spv[-1][1] <= 0:
                spv.pop()
            if bpv[-1][1] <= 0:
                bpv.pop()
        else:
            break

    expenditure = available_isk - current_isk

    return (total_profit, expenditure, volume)


# Calculate 1-location trips for each item and figure out how big the profit is
print('Calculating potential profit per 1-item, 1-trip...')
trade_to_profit = {}
item_counter = 1
for item, order_dict in analysis.items():
    print(f'Analyzing {item}... ({item_counter}/{len(analysis)})')
    for bo_location, bpv in order_dict['buy_orders'].items():
        for so_location, spv in order_dict['sell_orders'].items():
            profit, expenditure, volume = trade_until_oom_or_unprofitable(bpv, spv, available_isk)
            if expenditure == 0 or profit < minimum_profit:
                continue
            trade_to_profit[(item, so_location, bo_location)] = (profit, expenditure, volume)
    item_counter += 1

# Group all 1 item trips going on the same route a -> b
# TODO: Also include intermediate locations from "route" API route
print('Collecting profit by route...')
route_to_profit = {}
for trade, pev in trade_to_profit.items():
    item, a, b = trade
    profit, expenditure, volume = pev
    if (a, b) not in route_to_profit:
        route_to_profit[(a, b)] = {
            'profit': profit,
            'expenditure': expenditure,
            'trades': [(item, volume, profit, expenditure)],
        }
    else:
        route_to_profit[(a, b)]['profit'] += profit
        route_to_profit[(a, b)]['expenditure'] += expenditure
        route_to_profit[(a, b)]['trades'].append((item, volume, profit, expenditure))

print('Calculating route lengths...')

print('Spinning up API connection...')
from startup import Connection
conn = Connection()


def stations_to_system(stations):
    res = []
    for station in stations:
        if station.split(' ')[0] == 'Amarr':
            ans = 'Amarr'
        elif len(station.split('-')[0].split(' ')) == 2:
            ans = station.split('-')[0].strip(' ')
        else:
            ans = ' '.join(station.split('-')[0].split(' ')[:-2])
        res.append(ans)
    return res


systems_to_id_lookup = set()
for route in route_to_profit:
    a, b = stations_to_system(route)
    systems_to_id_lookup.add(a)
    systems_to_id_lookup.add(b)

# Method from https://stackoverflow.com/a/22045226/7247528
def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

batches = list(chunk(systems_to_id_lookup, 1000))
name_to_id = {}
for batch in batches:
    names = set(batch)
    res = conn.qq('Universe!##!post_universe_ids', names=batch)
    for system in res['systems']:
        if system['name'] in batch:
            name_to_id[system['name']] = system['id']

with open('data/known_shortest_routes.json', 'r') as f:
    known_shortest_routes = json.load(f)
known_shortest_routes = {eval(k): v for k, v in known_shortest_routes.items()}

for route in route_to_profit:
    a, b = stations_to_system(route)
    if (a, b) in known_shortest_routes:
        path = [1]*known_shortest_routes[(a, b)]
    else:
        path = conn.qq('Routes!##!get_route_origin_destination', origin=name_to_id[a], destination=name_to_id[b])
        known_shortest_routes[(a, b)] = len(path)

    route_to_profit[route]['systems'] = len(path)

known_shortest_routes = {str(k): v for k, v in known_shortest_routes.items()}
with open('data/known_shortest_routes.json', 'w') as f:
    json.dump(known_shortest_routes, f)


def userRound(number):
    # Display numbers nicely for end user (eg. 814.3k)
    # input int/float, return string
    cutoffs = {
        1_000_000_000: lambda x: f'{round(x/1_000_000_000, 2)}B',
        1_000_000: lambda x: f'{round(x/1_000_000, 2)}M',
        1_000: lambda x: f'{round(x/1_000, 2)}K',
        0: lambda x: f'{round(x, 2)}'
    }

    for n, roundfxn in cutoffs.items():
        if abs(number) >= n:
            rounded = roundfxn(number)
            return rounded

metric_raw_profit = lambda x: x[-1]['profit']
metric_profit_percent = lambda x: x[-1]['profit'] / x[-1]['expenditure']
metric_raw_profit_per_hour = lambda x: x[-1]['profit'] / (x[-1]['systems'] / 60)

route_to_profit = list(route_to_profit.items())
route_to_profit.sort(key=metric_raw_profit_per_hour, reverse=True)
for route, trade_data in route_to_profit[:20]:
    a, b = route
    expenditure, profit, trades, steps = trade_data['expenditure'], trade_data['profit'], trade_data['trades'], trade_data['systems']
    cprint(f'({a} -> {b}): {userRound(expenditure)} -> {userRound(expenditure+profit)} ({steps} systems or {userRound(profit/(steps/60))}ISK/hr)', 'green')
    for trade in trades:
        cprint(f'    {trade[1]} {trade[0]} {userRound(trade[3])} -> {userRound(trade[2] + trade[3])}', 'yellow')
    # print(f'{userRound(volume)} {item} : {userRound(expenditure)} -> {userRound(expenditure+profit)}')
