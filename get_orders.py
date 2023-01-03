# Want to find situations where:
#   - a buy order is available somewhere for more than...
#   - a sell order somewhere else
# (AKA free money, assuming you haul it from point A to point B)

from collections import defaultdict
from itertools import islice
import json
from startup import Connection
import pandas as pd
from pathlib import Path


trade_hub_regions = {
    'amarr': 10000043, # Domain
    'jita': 10000002, # The Forge
    'dodixie': 10000032, # Sinq Laison
    'rens': 10000030, # Heimatar
    'akiainavas': 10000016, # Lonetrek
    'clellinon': 10000068, # Verge Vendor
    'couster-oursalert': 10000064, # Essence
}
interesting_item_ids = [ # The full query is highly data limited, so have to select specific items of interest
    # Premium Goods
    40520, # Large Skill Injector
    45635, # Small Skill Injector
    44992, # PLEX

    # Ships
    33468, # Astero
    12005, # Ishtar
    29340, # Osprey Navy Issue
    17918, # Rattlesnake
    33681, # Gecko

    # Common Trade Goods
    33577, # Covert Research Tools
    25624, # Intact Armor Plates
    28606, # Orca
    52568, # HyperCore
    21815, # Elite Drone AI
    36, # Mexallon
    48927, # Chromodynamic Tricarboxyls
    11399, # Morphite
    39, # Zydrine

    # High trade volume from https://www.adam4eve.eu/tradeVol_type.php
    # Items above 20b trade volume in last 30 days
    # Extracted with https://regex101.com/r/thZt0o/1
    # ["PLEX", "Large Skill Injector", "Skill Extractor", "Sleeper Drone AI Nexus", "10M Bounty SCC Encrypted Bond", "Triglavian Survey Database", "Ancient Coordinates Database", "Warclone Blanks", "23rd Tier Overseer's Personal Effects", "Sleeper Data Library", "Paladin", "Isogen", "Orca", "Small Skill Injector", "Vargur", "Keepstar Upwell Quantum Core", "Golem", "Rhea", "Rogue Drone Infestation Data", "Marshal", "Gila", "Pithum A-Type Multispectrum Shield Hardener", "Charon", "Morphite", "Estamel's Modified Rapid Heavy Missile Launcher", "Expert Cerebral Accelerator", "Ark", "Amarr Titan", "Rorqual", "Pithum C-Type Multispectrum Shield Hardener", "Rattlesnake", "Nestor", "'Draccous' Fortizar", "Multiple Pilot Training Certificate", "Nyx", "19th Tier Overseer's Personal Effects", "Pith X-Type X-Large Shield Booster", "Paladin Sanguinary Savant SKIN", "Neural Network Analyzer", "Intact Armor Plates", "Nomad", "Obelisk", "'Prometheus' Fortizar", "Praxis", "Zydrine", "Unit W-634's Modified Damage Control", "Gist X-Type X-Large Shield Booster", "Vepas's Modified Multispectrum Shield Hardener", "Mexallon", "Kronos", "Ishtar", "Cormack's Modified Damage Control", "Bowhead", "Providence", "Anshar", "ORE Strip Miner", "Leshak", "Revelation", "Estamel's Modified Cruise Missile Launcher", "Thanatos", "Fortizar", "Fortizar Upwell Quantum Core", "Megacyte", "Naglfar", "21st Tier Overseer's Personal Effects", "Tobias' Modified Ballistic Control System", "Miasmos Quafe Ultramarine Edition", "Nocxium", "Nestor Yoiul Festival YC121 SKIN", "Caldari Navy Ballistic Control System", "Standup L-Set Reprocessing Monitor II", "Hel", "Tobias' Modified Heavy Warp Disruptor", "Machariel", "Gallente Titan", "Nidhoggur", "Barghest", "Apostle", "Athanor Upwell Quantum Core", "Minmatar Titan", "Daily Alpha Injector", "Caldari Titan", "Logic Circuit", "Nightmare", "Sotiyo", "Tengu", "Tatara Upwell Quantum Core", "Astero", "Azbel Upwell Quantum Core", "Cormack's Modified Magnetic Field Stabilizer", "Archon", "Corpum A-Type Multispectrum Energized Membrane", "Men's State Commander's Dress Jacket", "Loki", "Vindicator", "Chimera", "Moros", "Pyerite", "Draclira's Modified Large EMP Smartbomb", "CONCORD Rogue Analysis Beacon", "Fenrir", "Neodymium", "Medium Core Defense Field Extender II", "Phoenix", "Nanite Repair Paste", "Chelm's Modified Cap Recharger", "Pithum A-Type Medium Shield Booster", "Helium Isotopes", "Enhanced Ward Console", "Hulk", "Corpus X-Type Large Armor Repairer", "Tritanium", "Extended 'Radiance' Cerebral Accelerator", "Coreli A-Type Multispectrum Coating", "Republic Fleet Large Cap Battery", "Robotics", "Unit W-634's Modified Drone Damage Amplifier", "High-grade Crystal Omega", "Oxygen Isotopes", "Promethium", "Platinum", "Vizan's Modified Heat Sink", "Athanor", "Estamel's Modified Ballistic Control System", "Unit P-343554's Modified Fighter Support Unit", "Nitrogen Isotopes", "Imperial Navy Large EMP Smartbomb", "Zero-Point Condensate", "Dysprosium", "Genolution 'Auroral' AU-79", "Astrahus", "Covert Research Tools", "Neurovisual Input Matrix", "Stratios", "Centum A-Type Multispectrum Energized Membrane", "High-grade Amulet Omega", "Cerberus", "Gotan's Modified 800mm Repeating Cannon", "Covetor Blueprint", "Dominix", "Michi's Excavation Augmentor", "Bhaalgorn", "Imperial Navy Heat Sink", "Raitaru Upwell Quantum Core", "Retriever Blueprint", "Raven"]
    # Results from API are extracted by:
    # 1. , \{ -> \n{
    # 2. https://regex101.com/r/gH7aP2/1
    44992, # PLEX
    40519, # Skill Extractor
    30747, # Sleeper Drone AI Nexus
    55932, # 10M Bounty SCC Encrypted Bond
    48121, # Triglavian Survey Database
    30746, # Ancient Coordinates Database
    56788, # Warclone Blanks
    19421, # 23rd Tier Overseer's Personal Effects
    28659, # Paladin
    37, # Isogen
    28606, # Orca
    28665, # Vargur
    28710, # Golem
    17715, # Gila
    4347, # Pithum A-Type Multispectrum Shield Hardener
    20185, # Charon
    11399, # Morphite
    55826, # Expert Cerebral Accelerator
    4349, # Pithum C-Type Multispectrum Shield Hardener
    17918, # Rattlesnake
    33472, # Nestor
    34133, # Multiple Pilot Training Certificate
    19208, # Pith X-Type X-Large Shield Booster
    73454, # Paladin Sanguinary Savant SKIN
    30744, # Neural Network Analyzer
    25624, # Intact Armor Plates
    20187, # Obelisk
    47466, # Praxis
    39, # Zydrine
    36, # Mexallon
    28661, # Kronos
    12005, # Ishtar
    28754, # ORE Strip Miner
    40, # Megacyte
    19722, # Naglfar
    29984, # Tengu
    29990, # Loki
    35832, # Astrahus
    33577, # Covert Research Tools
    18883, # Centum A-Type Multispectrum Energized Membrane
    15810, # Imperial Navy Heat Sink
    40520, # Large Skill Injector
    30745, # Sleeper Data Library
    45635, # Small Skill Injector
    56207, # Keepstar Upwell Quantum Core
    28844, # Rhea
    60459, # Rogue Drone Infestation Data
    44996, # Marshal
    33454, # Estamel's Modified Rapid Heavy Missile Launcher
    28850, # Ark
    3347, # Amarr Titan
    28352, # Rorqual
    47513, # 'Draccous' Fortizar
    23913, # Nyx
    19417, # 19th Tier Overseer's Personal Effects
    28846, # Nomad
    47516, # 'Prometheus' Fortizar
    41211, # Unit W-634's Modified Damage Control
    19198, # Gist X-Type X-Large Shield Booster
    14766, # Vepas's Modified Multispectrum Shield Hardener
    41210, # Cormack's Modified Damage Control
    34328, # Bowhead
    20183, # Providence
    28848, # Anshar
    47271, # Leshak
    19720, # Revelation
    14678, # Estamel's Modified Cruise Missile Launcher
    23911, # Thanatos
    35833, # Fortizar
    56204, # Fortizar Upwell Quantum Core
    19419, # 21st Tier Overseer's Personal Effects
    14534, # Tobias' Modified Ballistic Control System
    4388, # Miasmos Quafe Ultramarine Edition
    38, # Nocxium
    49963, # Nestor Yoiul Festival YC121 SKIN
    15681, # Caldari Navy Ballistic Control System
    46640, # Standup L-Set Reprocessing Monitor II
    22852, # Hel
    14662, # Tobias' Modified Heavy Warp Disruptor
    17738, # Machariel
    3344, # Gallente Titan
    24483, # Nidhoggur
    33820, # Barghest
    37604, # Apostle
    56202, # Athanor Upwell Quantum Core
    3345, # Minmatar Titan
    46375, # Daily Alpha Injector
    3346, # Caldari Titan
    25619, # Logic Circuit
    17736, # Nightmare
    35827, # Sotiyo
    56205, # Tatara Upwell Quantum Core
    33468, # Astero
    56206, # Azbel Upwell Quantum Core
    15150, # Cormack's Modified Magnetic Field Stabilizer
    23757, # Archon
    18881, # Corpum A-Type Multispectrum Energized Membrane
    58933, # Men's State Commander's Dress Jacket
    17740, # Vindicator
    23915, # Chimera
    19724, # Moros
    14798, # Draclira's Modified Large EMP Smartbomb
    60244, # CONCORD Rogue Analysis Beacon
    20189, # Fenrir
    16651, # Neodymium
    31796, # Medium Core Defense Field Extender II
    19726, # Phoenix
    28668, # Nanite Repair Paste
    16605, # Chelm's Modified Cap Recharger
    19191, # Pithum A-Type Medium Shield Booster
    16274, # Helium Isotopes
    25625, # Enhanced Ward Console
    22544, # Hulk
    19045, # Corpus X-Type Large Armor Repairer
    72868, # Extended 'Radiance' Cerebral Accelerator
    18789, # Coreli A-Type Multispectrum Coating
    41218, # Republic Fleet Large Cap Battery
    9848, # Robotics
    32925, # Unit W-634's Modified Drone Damage Amplifier
    20161, # High-grade Crystal Omega
    17887, # Oxygen Isotopes
    16652, # Promethium
    16644, # Platinum
    14808, # Vizan's Modified Heat Sink
    35835, # Athanor
    14690, # Estamel's Modified Ballistic Control System
    32955, # Unit P-343554's Modified Fighter Support Unit
    17888, # Nitrogen Isotopes
    15963, # Imperial Navy Large EMP Smartbomb
    48112, # Zero-Point Condensate
    16650, # Dysprosium
    33329, # Genolution 'Auroral' AU-79
    30251, # Neurovisual Input Matrix
    33470, # Stratios
    20509, # High-grade Amulet Omega
    11993, # Cerberus
    14459, # Gotan's Modified 800mm Repeating Cannon
    17477, # Covetor Blueprint
    645, # Dominix
    20700, # Michi's Excavation Augmentor
    17920, # Bhaalgorn
    56203, # Raitaru Upwell Quantum Core
    17479, # Retriever Blueprint
    638, # Raven
]
interesting_item_ids = list(set(interesting_item_ids))

conn = Connection()

orders_path = Path('data/orders.csv')
df = None
if orders_path.exists():
    with open(orders_path, 'r') as f:
        df = pd.read_csv(f)
else:
    # Get market order data from API
    # TODO: Implement 300s timeout
    for hub_name, region in trade_hub_regions.items():
        print(f'Checking {hub_name}...')
        orders = []
        for item in interesting_item_ids:
            orders.extend(conn.qq('Market!##!get_markets_region_id_orders', region_id=region, type_id=item))
        
        if df is None:
            df = pd.DataFrame.from_records(orders)
        else:
            added = pd.DataFrame.from_records(orders)
            df = pd.concat([df, added])

    with open('data/orders.csv', 'w') as f:
        df.to_csv(f)


# Look up any unknown item names
with open('data/known_names.json', 'r') as f:
    known_names = json.load(f)

# Method from https://stackoverflow.com/a/22045226/7247528
def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

tolookup = set()
for order in df.itertuples():
    item_id = order.type_id
    location_id = order.location_id
    if str(item_id) not in known_names:
        tolookup.add(item_id)
    if str(location_id) not in known_names:
        tolookup.add(location_id)

print(f'{len(tolookup)} items to look up names for')
unknown_structures = []
if len(tolookup) > 0:
    universe_name_lookup_batches = [list(x) for x in chunk(tolookup, 1000)]
    for batch in universe_name_lookup_batches:
        res = conn.qq('Universe!##!post_universe_names', ids=batch)
        if 'error' in res:
            # For some reason market region ID orders returns structures we don't have access to
            # Filter these out an fix the order list in post
            error_ids = [int(x.split("'")[1]) for x in res['error'].split(',')[:-1]]
            unknown_structures.extend(error_ids)
            newbatch = list(set(batch) - set(error_ids))
            if len(newbatch) > 0:
                res = conn.qq('Universe!##!post_universe_names', ids=newbatch)
            else:
                continue

        known_names.update(
            {str(x['id']): x['name'] for x in res}
        )

    with open('data/known_names.json', 'w') as f:
        json.dump(known_names, f)

# Filter illegal access structures out of order data
unknown_structures = set(unknown_structures)
df = df[(~df['location_id'].isin(unknown_structures))]

# Group by items
# For specific format, see sample_analysis_layout.json
analysis = defaultdict(
    lambda: dict(
        buy_orders=defaultdict(lambda: defaultdict(int)),
        sell_orders=defaultdict(lambda: defaultdict(int)),
    )
)
for order in df.itertuples():
    item_id = order.type_id
    location_id = order.location_id
    price = order.price
    available_volume = order.volume_remain
    order_type = ['sell_orders', 'buy_orders'][order.is_buy_order]

    analysis[known_names[str(item_id)]][order_type][known_names[str(location_id)]][price] += available_volume

# Sort buy/sell orders
for item_id, orders in analysis.items():
    for order_type, locations in orders.items():
        for location, pricevol in locations.items():
            if order_type == 'buy_orders':
                analysis[item_id][order_type][location] = dict(sorted(pricevol.items(), reverse=True))
            elif order_type == 'sell_orders':
                analysis[item_id][order_type][location] = dict(sorted(pricevol.items()))

with open('data/analysis.json', 'w') as f:
    json.dump(analysis, f)