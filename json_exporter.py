#!/usr/bin/python3
# json_exporter.py - Reading json and exposing them to use in Prometheus
# Author: Sjors101 <https://github.com/sjors101/>, 08/22/2018

from prometheus_client import start_http_server, Gauge
from operator import itemgetter
from collections import OrderedDict
import json, requests, sys, time

log_file = "/var/log/json_exporter.log"


def collect_metrics(endpoint):
    try:
        # Fetch the JSON
        endpoint_metrics = json.loads(requests.get(endpoint, timeout=5).content.decode('UTF-8'))
        endpoint_metrics = OrderedDict(sorted(endpoint_metrics.items(), key=itemgetter(0)))

        # replace bad characters
        endpoint_metrics_new = {}
        replace_dict = {'.': '_', '-': '_'}
        for key, metrics in endpoint_metrics.items():
            for i, j in replace_dict.items():
                key = key.replace(i, j)
            endpoint_metrics_new[key] = metrics

        return endpoint_metrics_new

    except requests.Timeout:
        exception_error = 'ERROR, timeout, cannot access this endpoint, is the url correct?'
        return exception_error
    except requests.exceptions.ConnectionError:
        exception_error = 'ERROR, cannot connect to endpoint, is it down?'
        return exception_error
    except json.decoder.JSONDecodeError:
        exception_error = 'ERROR, this is not JSON, is the url correct?'
        return exception_error
    except:
        exception_error = "ERROR, unexpected:", sys.exc_info()[0]
        return exception_error


def set_gauge(endpoint_metrics):
    # set gauge before starting http_server
    gauge_list = list()
    for key, metrics in endpoint_metrics.items():
        gauge_list.append(Gauge(key, "- This metric is exposed via json_exporter.py"))
    return gauge_list


def logger(log_file, log_message):
    date = (time.asctime())
    log_file = open(log_file, 'w+')
    log_file.write(' '.join((date, ':', log_message, '\n')))
    log_file.close()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("ERROR, feed me more arguments")
        print("Usage: json_exporter.py <port> <http://endpoint/metrics>")
    else:
        endpoint_metrics = collect_metrics(sys.argv[2])
        if "ERROR" in endpoint_metrics:
            print (endpoint_metrics)
            exit()
        else:
            gauge_list = set_gauge(endpoint_metrics)
            start_http_server(int(sys.argv[1]))

        while True:
            endpoint_metrics = collect_metrics(sys.argv[2])

            if "ERROR" in endpoint_metrics:
                logger(log_file, endpoint_metrics)
            else:
                micro_count = 0
                for gauge in gauge_list:
                    metric = (list(endpoint_metrics.values())[micro_count])
                    gauge.set(metric)
                    micro_count += 1

            time.sleep(10)
