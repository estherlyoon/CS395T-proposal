package main

import (
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

const (
	proxyPort      = 8000
	alpha          = 0.15
	requestTimeout = 10 * time.Second
)

var servicePort, _ = strconv.Atoi(os.Getenv("SERVICE_PORT"))

var inflightRequestGauge = prometheus.NewGauge(
	prometheus.GaugeOpts{
		Name: "inflight_requests",
		Help: "The number of requests currently inflight (effectively, queue length) at the given pod",
	},
)

var requestLatencyGauge = prometheus.NewGauge(
	prometheus.GaugeOpts{
		Name: "request_latency",
		Help: "Exponential moving average of request latency at this pod",
	},
)

var requestLatencyGaugeValue = 0.

// Create a structure to define the proxy functionality.
type Proxy struct{}

var promHandler = promhttp.Handler()

func (p *Proxy) forwardRequest(req *http.Request) (*http.Response, error) {
	// Prepare the destination endpoint to forward the request to.
	fmt.Fprintln(os.Stderr, req.RequestURI)
	proxyUrl := fmt.Sprintf("http://127.0.0.1:%d%s", servicePort, req.URL.RequestURI())

	// Create an HTTP client and a proxy request based on the original request.
	httpClient := http.Client{Timeout: requestTimeout}
	proxyReq, err := http.NewRequest(req.Method, proxyUrl, req.Body)

	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		return nil, err
	}

	// Capture the duration while making a request to the destination service.
	start := time.Now()
	inflightRequestGauge.Inc()
	res, err := httpClient.Do(proxyReq)
	inflightRequestGauge.Dec()
	latency := time.Since(start).Seconds()

	fmt.Fprintln(os.Stderr, "request", proxyUrl, "took", latency, "seconds with status", res.StatusCode)

	requestLatencyGaugeValue = alpha*requestLatencyGaugeValue + (1.-alpha)*latency
	requestLatencyGauge.Set(requestLatencyGaugeValue)

	// Return the response, the request duration, and the error.
	return res, err
}

func (p *Proxy) writeResponse(w http.ResponseWriter, res *http.Response) {
	// Copy all the header values from the response.
	for name, values := range res.Header {
		w.Header()[name] = values
	}

	// Set a special header to notify that the proxy actually serviced the request.
	w.Header().Set("Server", "sidecar-proxy")

	// Set the status code returned by the destination service.
	w.WriteHeader(res.StatusCode)

	// Copy the contents from the response body.
	io.Copy(w, res.Body)

	// Finish the request.
	res.Body.Close()
}

var prometheusAuthorization = fmt.Sprintf("Basic %s", base64.StdEncoding.EncodeToString([]byte("prometheus:prometheus")))

func (p *Proxy) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	if auth, ok := req.Header["Authorization"]; ok &&
		auth[0] == prometheusAuthorization &&
		req.RequestURI == "/metrics" {

		promHandler.ServeHTTP(w, req)
		return
	}
	// Forward the HTTP request to the destination service.
	res, err := p.forwardRequest(req)

	// Notify the client if there was an error while forwarding the request.
	if err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	// If the request was forwarded successfully, write the response back to
	// the client.
	p.writeResponse(w, res)
}

func main() {
	// prometheus.Unregister()
	prometheus.MustRegister(requestLatencyGauge)
	prometheus.MustRegister(inflightRequestGauge)
	inflightRequestGauge.Set(0)
	http.ListenAndServe(fmt.Sprintf(":%d", proxyPort), &Proxy{})
}
