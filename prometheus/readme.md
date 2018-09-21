# Prometheus

These are dev prometheus setup to see Idunn's metric.
This is absolutly not to be used in production!

To test it, you need to run the idunn's docker-compose with the additional prometheus compose.
In the main idunn's directory:

`docker-compose -f docker-compose.yml -f prometheus/prometheus-compose.yml up --build`

Then you can query idunn on `localhost:5000` and access graphana on `http://localhost:3000/d/idunn_1/idunn-dashboard`.

(graphana's accesses are user: `admin`, password: `admin`).

If you change the dashboard, don't forget to export to json  and change the file `graphana_dashboards.json`.
