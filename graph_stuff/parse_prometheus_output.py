import pickle

with open("../artifacts/latest/prometheus.log.pickle", 'rb') as f:
    avg_inflight, avg_latency, num_replicas = pickle.load(f)

nonzero_avg_inflight = [app['metric']['app'] for app in avg_inflight if any([float(point) > 0 for _, point in app['values']])]
print(nonzero_avg_inflight, "have nonzero average inflights requests at some point")

