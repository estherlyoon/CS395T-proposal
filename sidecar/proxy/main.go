package main

import (
	"encoding/base64"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

const (
	proxyPort   = 8000
	servicePort = 80
	serviceName = "SERVICE_NAME"
)

var inflightRequestGauge = prometheus.NewGauge(
	prometheus.GaugeOpts{
		Name: fmt.Sprintf("%s_inflight_requests", serviceName),
		Help: fmt.Sprintf("The number of requests currently inflight (effectively, queue length) at service %s", serviceName),
	},
)

// Create a structure to define the proxy functionality.
type Proxy struct{}

var promHandler = promhttp.Handler()

func (p *Proxy) forwardRequest(req *http.Request) (*http.Response, time.Duration, error) {
	// Prepare the destination endpoint to forward the request to.
	proxyUrl := fmt.Sprintf("http://127.0.0.1:%d%s", servicePort, req.RequestURI)

	// Create an HTTP client and a proxy request based on the original request.
	httpClient := http.Client{}
	proxyReq, _ := http.NewRequest(req.Method, proxyUrl, req.Body)

	// Capture the duration while making a request to the destination service.
	start := time.Now()
	inflightRequestGauge.Inc()
	res, err := httpClient.Do(proxyReq)
	inflightRequestGauge.Dec()
	duration := time.Since(start)

	// Return the response, the request duration, and the error.
	return res, duration, err
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
	res, _, err := p.forwardRequest(req)

	// Notify the client if there was an error while forwarding the request.
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}

	// If the request was forwarded successfully, write the response back to
	// the client.
	p.writeResponse(w, res)
}

func main() {
	// prometheus.Unregister()
	prometheus.MustRegister(inflightRequestGauge)
	http.ListenAndServe(fmt.Sprintf(":%d", proxyPort), &Proxy{})
}
