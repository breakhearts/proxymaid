from proxymaid.proxypoolservice import start_proxy_pool_service
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', dest='interval', type=float, help='minimum seconds reuse a proxy')
    parser.add_argument('-l', dest='latency', type=float, help='max latency when a proxy available')
    parser.add_argument('-n', dest='max_unavailable_count', type=int,
                        help='maximum unavailable count of a proxy, if exceed this count, proxy will be delete from pool')
    args = parser.parse_args()
    kwargs = {}
    if args.interval:
        if args.interval:kwargs["interval_second"] = args.interval
        if args.interval:kwargs["max_latency"] = args.latency
        if args.max_unavailable_count:kwargs["max_unavailable_count"] = args.max_unavailable_count
    start_proxy_pool_service(**kwargs)