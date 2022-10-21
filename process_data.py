# %%
# Create sample train and test keys
import sys
import os

data_name = sys.argv[1]
data_proccessed_dir = "data_processed/%s" % data_name

# %%
import networkx as nx

def read_graphs(database_file_name):
    graphs = dict()
    sizes = {}
    degrees = {}

    with open(database_file_name, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
        tgraph, graph_cnt = None, 0
        for i, line in enumerate(lines):
            cols = line.split(' ')
            if cols[0] == 't':
                if tgraph is not None:
                    graphs[graph_cnt] = tgraph
                    sizes[graph_cnt] = tgraph.number_of_nodes()
                    degrees[graph_cnt] = sum(dict(tgraph.degree).values()) / sizes[graph_cnt]

                    tgraph = None
                if cols[-1] == '-1':
                    break

                tgraph = nx.Graph()
                graph_cnt = int(cols[2])

            elif cols[0] == 'v':
                tgraph.add_node(int(cols[1]), label=int(cols[2]))

            elif cols[0] == 'e':
                tgraph.add_edge(int(cols[1]), int(cols[2]), label=int(cols[3]))

        # adapt to input files that do not end with 't # -1'
        if tgraph is not None:
            graphs[graph_cnt] = tgraph
            sizes[graph_cnt] = tgraph.number_of_nodes()
            degrees[graph_cnt] = sum(dict(tgraph.degree).values()) / sizes[graph_cnt]

    return graphs, sizes, degrees

def read_mapping(filename):
    mapping = {}
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]
        tmapping, graph_cnt = None, 0
        for i, line in enumerate(lines):
            cols = line.split(' ')
            if cols[0] == 't':
                if tmapping is not None:
                    mapping[graph_cnt] = tmapping
                    
                if cols[-1] == '-1':
                    break

                tmapping = []
                graph_cnt = int(cols[2])

            elif cols[0] == 'v':
                tmapping.append((int(cols[1]), int(cols[2])))

        if tmapping is not None:
            mapping[graph_cnt] = tmapping

    return mapping

def load_graph_data(data_dir, source_id):
    
    source_graph = read_graphs("%s/%s/source.lg" % (data_dir, source_id))[0][int(source_id)]
    iso_subgraphs, iso_sizes, iso_degrees = read_graphs("%s/%s/iso_subgraphs.lg" % (data_dir, source_id))
    noniso_subgraphs, noniso_sizes, noniso_degrees = read_graphs("%s/%s/noniso_subgraphs.lg" % (data_dir, source_id))
    iso_subgraphs_mapping = read_mapping("%s/%s/iso_subgraphs_mapping.lg" % (data_dir, source_id))
    noniso_subgraphs_mapping = read_mapping("%s/%s/noniso_subgraphs_mapping.lg" % (data_dir, source_id))
    return source_graph, iso_subgraphs, noniso_subgraphs, iso_subgraphs_mapping, \
           noniso_subgraphs_mapping, iso_sizes, noniso_sizes, iso_degrees, noniso_degrees

# %%
import pickle
from tqdm import tqdm

# Load and save
def load_dataset(data_dir, list_source, save_dir, additional_tag=""):
    size_dict = {}
    degree_dict = {}

    for source_id in tqdm(list_source):
        graph, iso_subgraphs, noniso_subgraphs, \
            iso_subgraphs_mapping, noniso_subgraphs_mapping, \
                iso_sizes, noniso_sizes, \
                iso_degrees, noniso_degrees = load_graph_data(data_dir, source_id)
        
        for key, data in iso_subgraphs.items():
            fname = "%s_%d_iso_%s" % (source_id, key, additional_tag)
            size_dict[fname] = iso_sizes[key]
            degree_dict[fname] = iso_degrees[key]
            with open(f"{save_dir}/{fname}", 'wb') as f:
                pickle.dump([data, graph, iso_subgraphs_mapping[key]], f)
        
        for key, data in noniso_subgraphs.items():
            fname = "%s_%d_non_%s" % (source_id, key, additional_tag)
            size_dict[fname] = noniso_sizes[key]
            degree_dict[fname] = noniso_degrees[key]
            with open(f"{save_dir}/{fname}", 'wb') as f:
                pickle.dump([data, graph, noniso_subgraphs_mapping[key]], f)

    pickle.dump(size_dict, open(f"{save_dir}/subgraphs_size.pkl", "wb"))
    pickle.dump(degree_dict, open(f"{save_dir}/subgraphs_degree.pkl", "wb"))

# Load data
if not os.path.exists(data_proccessed_dir):
        os.mkdir(data_proccessed_dir)

# %%
if sys.argv[2] == "synthesis":
    data_dir = "data_%s/datasets/%s" % (sys.argv[2], data_name)

    list_source = os.listdir(data_dir)
    list_source = list(filter(lambda x: os.path.isdir(os.path.join(data_dir, x)), list_source))

    load_dataset(data_dir, list_source, data_proccessed_dir)

    # Split train test
    from sklearn.model_selection import train_test_split
    train_source, test_source = train_test_split(list_source, test_size=0.2, random_state=42)
    valid_keys = os.listdir(data_proccessed_dir)

    train_keys = [k for k in valid_keys if k.split('_')[0] in train_source]    
    test_keys = [k for k in valid_keys if k.split('_')[0] in test_source]  

elif sys.argv[2] == "real":
    data_dir = "data_%s/datasets/%s" % (sys.argv[2], data_name + "_test")
    list_source = os.listdir(data_dir)
    list_source = list(filter(lambda x: os.path.isdir(os.path.join(data_dir, x)), list_source))

    load_dataset(data_dir, list_source, data_proccessed_dir, additional_tag="test")
    test_keys = os.listdir(data_proccessed_dir)
    
    data_dir_train = "data_%s/datasets/%s" % (sys.argv[2], data_name + "_train")
    list_source_train = os.listdir(data_dir_train)
    list_source_train = list(filter(lambda x: os.path.isdir(os.path.join(data_dir_train, x)), list_source_train))

    load_dataset(data_dir_train, list_source_train, data_proccessed_dir, additional_tag="train")
    train_keys = list(set(os.listdir(data_proccessed_dir)) - set(test_keys))

# Notice that key which has "iso" is isomorphism, otherwise non-isomorphism

# %%
# Save train and test keys
import pickle

with open("%s/train_keys.pkl"%data_proccessed_dir, 'wb') as f:
    pickle.dump(train_keys, f)
    
with open("%s/test_keys.pkl"%data_proccessed_dir, 'wb') as f:
    pickle.dump(test_keys, f)

size_dict = pickle.load(open(f"{data_proccessed_dir}/subgraphs_size.pkl", "rb"))
degree_dict = pickle.load(open(f"{data_proccessed_dir}/subgraphs_degree.pkl", "rb"))

nondense_0_20 = list(filter(lambda x: size_dict[x] <= 20 and degree_dict[x] <= 3, test_keys))
nondense_20_40 = list(filter(lambda x: size_dict[x] > 20 and size_dict[x] <= 40 and degree_dict[x] <= 3, test_keys))
nondense_40_60 = list(filter(lambda x: size_dict[x] > 40 and size_dict[x] <= 60 and degree_dict[x] <= 3, test_keys))
nondense_60_ = list(filter(lambda x: size_dict[x] >= 60 and degree_dict[x] <= 3, test_keys))

dense_0_20 = list(filter(lambda x: size_dict[x] <= 20 and degree_dict[x] > 3, test_keys))
dense_20_40 = list(filter(lambda x: size_dict[x] > 20 and size_dict[x] <= 40 and degree_dict[x] > 3, test_keys))
dense_40_60 = list(filter(lambda x: size_dict[x] > 40 and size_dict[x] <= 60 and degree_dict[x] > 3, test_keys))
dense_60_ = list(filter(lambda x: size_dict[x] >= 60 and degree_dict[x] > 3, test_keys))


with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "nondense_0_20"), 'wb') as f:
    pickle.dump(nondense_0_20, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "nondense_20_40"), 'wb') as f:
    pickle.dump(nondense_20_40, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "nondense_40_60"), 'wb') as f:
    pickle.dump(nondense_40_60, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "nondense_60_"), 'wb') as f:
    pickle.dump(nondense_60_, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "dense_0_20"), 'wb') as f:
    pickle.dump(dense_0_20, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "nondense_20_40"), 'wb') as f:
    pickle.dump(dense_20_40, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "dense_40_60"), 'wb') as f:
    pickle.dump(dense_40_60, f)

with open("%s/test_keys_%s.pkl"%(data_proccessed_dir, "dense_0_20"), 'wb') as f:
    pickle.dump(dense_60_, f)
